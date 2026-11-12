"""Configurações 1 (modelo puro) e 2 (RAG simples), mais as peças comuns de validação."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from pydantic import ValidationError

from . import busca, config, ollama, prompts
from .base import carregar_fontes, trecho_por_id
from .esquema import SCHEMA_FUNDAMENTADO, SCHEMA_PURO, SaidaLLM, recusa


@dataclass
class Resposta:
    config: str
    saida: dict  # nao_consta, recomendacao, fonte (contrato do produto)
    motivo: str  # por que saiu assim (ver MOTIVOS)
    json_valido: bool  # a primeira saída do modelo já era um JSON no formato certo
    segundos: float = 0.0
    evidencia: str = ""  # frase da base que o modelo apontou como sustentação
    trechos: list = field(default_factory=list)  # [(trecho_id, score)] recuperados
    score_top1: float | None = None
    limiar: float | None = None
    passos: list = field(default_factory=list)  # chamadas de ferramenta do agente
    bruto: str = ""

    def como_dict(self) -> dict:
        return asdict(self)


MOTIVOS = {
    "resposta": "o modelo respondeu e a citação foi conferida contra os trechos que ele recebeu",
    "resposta_sem_verificacao": "o modelo respondeu sem base para conferir (modelo puro)",
    "recusa_limiar": "a busca não achou trecho parecido o bastante; o modelo nem foi chamado",
    "recusa_modelo": "o modelo disse que não tem como responder com o que recebeu",
    "recusa_citacao_invalida": "o modelo citou uma fonte que não recebeu; a resposta foi descartada",
    "recusa_sem_evidencia": "o agente não reuniu nenhuma evidência citável",
    "recusa_valor_divergente": "a recomendação citou um valor em reais diferente do que veio no resumo da loja",
    "json_invalido": "o modelo não devolveu um JSON no formato do contrato",
}


def interpretar(bruto: str) -> SaidaLLM | None:
    try:
        return SaidaLLM.model_validate(json.loads(bruto))
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None


def titulo_canonico(trecho_id: str) -> str | None:
    """Nome do documento de origem, tirado da base e não do que o modelo escreveu."""
    trecho = trecho_por_id(trecho_id)
    if trecho is None:
        return None
    return carregar_fontes()[trecho.doc_id]["titulo"]


def gerar_json(mensagens: list[dict], schema: dict, formato: str) -> tuple[SaidaLLM | None, bool, str, float]:
    """Chama o modelo pedindo o JSON do contrato; tenta mais uma vez se vier inválido."""
    r = ollama.chat(mensagens, formato=schema)
    bruto = r["mensagem"].get("content", "")
    segundos = r["segundos"]
    saida = interpretar(bruto)
    valido_de_primeira = saida is not None
    if saida is None:
        mensagens = mensagens + [
            {"role": "assistant", "content": bruto},
            {"role": "user", "content": "A resposta não seguiu o formato. " + formato},
        ]
        r = ollama.chat(mensagens, formato=schema)
        bruto = r["mensagem"].get("content", "")
        segundos += r["segundos"]
        saida = interpretar(bruto)
    return saida, valido_de_primeira, bruto, segundos


def saida_do_contrato(saida: SaidaLLM, titulo: str | None = None) -> dict:
    """Converte a saída do modelo para o contrato do produto (sem o campo evidencia)."""
    if saida.nao_consta:
        return recusa()
    d = {"nao_consta": False, "recomendacao": saida.recomendacao.strip(), "fonte": None}
    if saida.fonte:
        d["fonte"] = {"titulo": titulo or saida.fonte.titulo, "trecho_id": saida.fonte.trecho_id}
    return d


# ------------------------------------------------------------ 1. modelo puro
def responder_puro(pergunta: str) -> Resposta:
    mensagens = [
        {"role": "system", "content": prompts.SISTEMA_PURO},
        {"role": "user", "content": pergunta},
    ]
    saida, valido, bruto, segundos = gerar_json(mensagens, SCHEMA_PURO, prompts.FORMATO_PURO)
    if saida is None:
        return Resposta("puro", recusa(), "json_invalido", False, segundos, bruto=bruto)
    motivo = "recusa_modelo" if saida.nao_consta else "resposta_sem_verificacao"
    return Resposta("puro", saida_do_contrato(saida), motivo, valido, segundos, bruto=bruto)


# ------------------------------------------------------------ 2. RAG simples
def responder_rag(pergunta: str, resumo_loja: dict | None = None, consulta: str | None = None) -> Resposta:
    """Busca os trechos mais parecidos e pede a resposta fundamentada neles.

    resumo_loja: usado só na geração em lote, quando o resumo já vem na entrada.
    consulta: texto usado na busca, se for diferente da pergunta.
    """
    limiar = config.limiar_recusa()
    resultados = busca.buscar(consulta or pergunta)
    trechos = [(r.trecho.id, round(r.score, 4)) for r in resultados]
    top1 = resultados[0].score if resultados else 0.0
    comum = dict(trechos=trechos, score_top1=round(top1, 4), limiar=limiar)

    if top1 < limiar:
        return Resposta("rag", recusa(), "recusa_limiar", True, 0.0, **comum)

    conteudo = prompts.bloco_trechos(resultados)
    if resumo_loja is not None:
        conteudo += "\n<resumo_da_loja>\n" + json.dumps(resumo_loja, ensure_ascii=False) + "\n</resumo_da_loja>"
    conteudo += f"\n<pergunta>\n{pergunta}\n</pergunta>"
    mensagens = [{"role": "system", "content": prompts.SISTEMA_RAG}, {"role": "user", "content": conteudo}]

    saida, valido, bruto, segundos = gerar_json(mensagens, SCHEMA_FUNDAMENTADO, prompts.FORMATO)
    if saida is None:
        return Resposta("rag", recusa(), "json_invalido", False, segundos, bruto=bruto, **comum)
    if saida.nao_consta:
        return Resposta("rag", recusa(), "recusa_modelo", valido, segundos, bruto=bruto, **comum)

    permitidos = {t for t, _ in trechos}
    if saida.fonte is None or saida.fonte.trecho_id not in permitidos:
        # Uma segunda chance, dizendo exatamente quais identificadores valem.
        mensagens += [
            {"role": "assistant", "content": bruto},
            {
                "role": "user",
                "content": "O trecho_id citado não está entre os trechos fornecidos. Use exatamente um destes: "
                + ", ".join(sorted(permitidos))
                + ". Se nenhum sustenta a resposta, devolva nao_consta=true.",
            },
        ]
        saida2, _, bruto, s2 = gerar_json(mensagens, SCHEMA_FUNDAMENTADO, prompts.FORMATO)
        segundos += s2
        if saida2 is None or saida2.nao_consta or saida2.fonte is None or saida2.fonte.trecho_id not in permitidos:
            motivo = "recusa_modelo" if (saida2 is not None and saida2.nao_consta) else "recusa_citacao_invalida"
            return Resposta("rag", recusa(), motivo, valido, segundos, bruto=bruto, **comum)
        saida = saida2

    titulo = titulo_canonico(saida.fonte.trecho_id)
    return Resposta(
        "rag", saida_do_contrato(saida, titulo), "resposta", valido, segundos, evidencia=saida.evidencia, bruto=bruto, **comum
    )
