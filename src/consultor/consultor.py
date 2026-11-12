"""Ponto de entrada único: escolhe a configuração e devolve a resposta no contrato do produto."""
from __future__ import annotations

from .agente import responder_agente
from .geracao import MOTIVOS, Resposta, responder_puro, responder_rag

CONFIGURACOES = {
    "puro": responder_puro,
    "rag": responder_rag,
    "agente": responder_agente,
}


def responder(pergunta: str, configuracao: str = "agente") -> Resposta:
    if configuracao not in CONFIGURACOES:
        raise ValueError(f"configuração desconhecida: {configuracao}. Use uma de {sorted(CONFIGURACOES)}")
    return CONFIGURACOES[configuracao](pergunta)


def explicar(resposta: Resposta) -> dict:
    """Resumo legível de como a resposta foi produzida (transparência para o comerciante)."""
    return {
        "configuracao": resposta.config,
        "decisao": resposta.motivo,
        "decisao_explicada": MOTIVOS.get(resposta.motivo, ""),
        "trechos_consultados": [{"trecho_id": t, "similaridade": s} for t, s in resposta.trechos],
        "similaridade_melhor_trecho": resposta.score_top1,
        "limiar_de_recusa": resposta.limiar,
        "ferramentas_usadas": [
            {"ferramenta": p["ferramenta"], "argumentos": p["argumentos"]} for p in resposta.passos
        ],
        "segundos": round(resposta.segundos, 2),
    }
