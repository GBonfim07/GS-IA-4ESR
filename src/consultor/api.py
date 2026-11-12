"""API local do Consultor de Eficiência Energética.

    uvicorn consultor.api:app --app-dir src --host 127.0.0.1 --port 8000

Segurança e LGPD:
  - escuta só em 127.0.0.1 por padrão; a LLM e os dados não saem da máquina;
  - se CONSULTOR_API_KEY estiver definida, as rotas de geração exigem o cabeçalho X-API-Key;
  - a pergunta tem tamanho limitado e nunca é gravada em disco; o log guarda só um hash dela;
  - toda resposta traz a fonte citada e uma explicação de como foi produzida.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import __version__, config, ollama
from . import consultor as nucleo
from .base import carregar_trechos, trecho_por_id
from .esquema import Recomendacao
from .lote import recomendar_linha
from .resumo import ler_resumo

log = logging.getLogger("consultor.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="Consultor de Eficiência Energética",
    description="Componente de IA generativa do produto Energia que dá Lucro. LLM local com base de conhecimento.",
    version=__version__,
)


def exigir_chave(x_api_key: str | None = Header(default=None)) -> None:
    if config.API_KEY and not hmac.compare_digest(x_api_key or "", config.API_KEY):
        raise HTTPException(status_code=401, detail="Chave de API ausente ou inválida.")


class Pedido(BaseModel):
    pergunta: str = Field(min_length=3, max_length=config.MAX_CARACTERES_PERGUNTA)
    configuracao: Literal["puro", "rag", "agente"] = "agente"
    loja_id: str | None = Field(default=None, max_length=40)
    periodo: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class LinhaResumo(BaseModel):
    """Uma linha de por_equipamento. Os campos são validados porque entram no pedido feito à LLM."""

    equipamento_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    tipo: Literal["porta_aberta", "luz_acesa_sem_necessidade", "temperatura_alta"]
    eventos: int = Field(ge=0)
    duracao_total_s: float = Field(ge=0)
    kwh: float = Field(ge=0)
    custo_rs: float = Field(ge=0)


class ResumoLoja(BaseModel):
    por_equipamento: list[LinhaResumo] = Field(min_length=1, max_length=20)


class PedidoResumo(BaseModel):
    """Resumo no formato do GET /summary do painel. Se vier só loja_id e periodo, o resumo é lido de dados/."""

    loja_id: str = Field(max_length=40)
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$")
    resumo: ResumoLoja | None = None
    max_recomendacoes: int = Field(default=3, ge=1, le=5)


class RespostaAPI(Recomendacao):
    explicacao: dict


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if ollama.disponivel() else "ollama_indisponivel",
        "modelo_llm": config.MODELO_LLM,
        "modelo_embedding": config.MODELO_EMBEDDING,
        "trechos_na_base": len(carregar_trechos()),
        "limiar_de_recusa": config.limiar_recusa(),
        "versao": __version__,
    }


@app.post("/recomendar", response_model=RespostaAPI, dependencies=[Depends(exigir_chave)])
def recomendar(pedido: Pedido) -> RespostaAPI:
    """Recebe uma pergunta do comerciante e devolve a recomendação no contrato do produto."""
    try:
        r = nucleo.responder(pedido.pergunta, pedido.configuracao)
    except ollama.OllamaIndisponivel as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    log.info("recomendar pergunta=%s config=%s decisao=%s seg=%.1f", _hash(pedido.pergunta), r.config, r.motivo, r.segundos)
    return RespostaAPI(loja_id=pedido.loja_id, periodo=pedido.periodo, **r.saida, explicacao=nucleo.explicar(r))


@app.post("/recomendar/resumo", response_model=list[RespostaAPI], dependencies=[Depends(exigir_chave)])
def recomendar_por_resumo(pedido: PedidoResumo) -> list[RespostaAPI]:
    """Recebe o resumo de desperdício de uma loja e devolve uma recomendação para cada vilão do mês."""
    resumo = pedido.resumo.model_dump() if pedido.resumo else ler_resumo(pedido.loja_id, pedido.periodo)
    if not resumo or not resumo.get("por_equipamento"):
        raise HTTPException(status_code=404, detail="Resumo não encontrado para essa loja e período.")
    respostas = []
    try:
        for linha in resumo["por_equipamento"][: pedido.max_recomendacoes]:
            r = recomendar_linha(linha)
            respostas.append(
                RespostaAPI(loja_id=pedido.loja_id, periodo=pedido.periodo, **r.saida, explicacao=nucleo.explicar(r))
            )
    except ollama.OllamaIndisponivel as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    log.info("recomendar_resumo loja=%s periodo=%s n=%d", pedido.loja_id, pedido.periodo, len(respostas))
    return respostas


@app.get("/trechos/{trecho_id}")
def ver_trecho(trecho_id: str) -> dict:
    """Mostra o trecho citado, para o comerciante (ou o avaliador) conferir a fonte."""
    from .base import carregar_fontes

    trecho = trecho_por_id(trecho_id)
    if trecho is None:
        raise HTTPException(status_code=404, detail="Trecho não encontrado na base.")
    fonte = carregar_fontes()[trecho.doc_id]
    return {
        "trecho_id": trecho.id,
        "titulo": trecho.titulo,
        "texto": trecho.texto,
        "localizador": trecho.localizador,
        "documento": fonte["titulo"],
        "orgao": fonte["orgao"],
        "url": fonte["url"],
        "licenca": fonte["licenca"],
    }
