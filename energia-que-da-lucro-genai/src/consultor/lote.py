"""Geração em lote: do resumo de desperdício de uma loja para o JSON que o painel exibe.

Para cada equipamento que mais desperdiçou no mês, monta uma pergunta e uma consulta de busca
a partir da linha do resumo e pede uma recomendação fundamentada (RAG com o resumo no contexto).
"""
from __future__ import annotations

import re

from .esquema import recusa
from .geracao import Resposta, responder_rag
from .resumo import ler_resumo

_DESCRICAO = {
    "porta_aberta": "ficou com a porta aberta por tempo demais",
    "luz_acesa_sem_necessidade": "ficou com a luz acesa sem necessidade",
    "temperatura_alta": "registrou temperatura alta",
}

_CONSULTA = {
    "porta_aberta": "porta de expositor ou freezer aberta por muito tempo: por que gasta energia e como reduzir (vedação, hábito)",
    "luz_acesa_sem_necessidade": "luz acesa sem ninguém no ambiente: como evitar (sensor de presença, desligar)",
    "temperatura_alta": "temperatura alta no equipamento de refrigeração: causas e conservação dos alimentos",
}


def _reais(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def pergunta_do_equipamento(linha: dict) -> str:
    horas = linha["duracao_total_s"] / 3600
    valor = _reais(linha["custo_rs"])
    return (
        f"No período, o equipamento {linha['equipamento_id']} {_DESCRICAO.get(linha['tipo'], linha['tipo'])}: "
        f"{linha['eventos']} ocorrências, {horas:.1f} horas no total, {linha['kwh']} kWh e R$ {valor} de "
        f"desperdício estimado, somando todas as ocorrências do período. Escreva uma recomendação curta, "
        f"falando direto com o comerciante (use 'você'), com uma ação que ataque exatamente esse tipo de "
        f"desperdício. Cite o equipamento e diga que o desperdício estimado no período foi de R$ {valor}. "
        f"Esse valor é o total do período: não diga que é por ocorrência nem por mês, e não prometa economia. "
        f"Não suponha nada sobre a loja além do que está no resumo."
    )


def consulta_do_equipamento(linha: dict) -> str:
    return _CONSULTA.get(linha["tipo"], linha["tipo"])


def valores_conferem(texto: str, custo_rs: float) -> bool:
    """Todo valor em reais citado na recomendação tem de ser o custo que veio no resumo."""
    citados = re.findall(r"R\$\s*(\d+(?:[.,]\d+)?)", texto)
    return all(abs(float(v.replace(",", ".")) - custo_rs) < 0.005 for v in citados)


def recomendar_linha(linha: dict) -> Resposta:
    """Recomendação para uma linha do resumo, com conferência do valor em reais."""
    r = responder_rag(pergunta_do_equipamento(linha), resumo_loja=linha, consulta=consulta_do_equipamento(linha))
    if not r.saida["nao_consta"] and not valores_conferem(r.saida["recomendacao"], linha["custo_rs"]):
        r.saida, r.motivo = recusa(), "recusa_valor_divergente"
    return r


def recomendacoes_da_loja(loja_id: str, periodo: str, maximo: int = 3) -> list[tuple[dict, Resposta]]:
    resumo = ler_resumo(loja_id, periodo)
    if not resumo:
        return []
    return [(linha, recomendar_linha(linha)) for linha in resumo["por_equipamento"][:maximo]]
