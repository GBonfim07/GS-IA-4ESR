"""Resumo de desperdício de uma loja.

Por padrão lê os arquivos simulados em dados/. Se a variável PAINEL_URL estiver definida,
tenta primeiro o GET /summary do painel e cai no arquivo se ele estiver fora do ar ou
devolver algo fora do formato.

O painel publicado (repositório devops-energia) usa nomes de campos diferentes dos arquivos
de dados/. normalizar_resumo converte um formato no outro; o mapeamento está em
docs/contrato_de_dados.md.
"""
from __future__ import annotations

import json
import os
import re

import requests

from . import config

LOJAS = ("padaria-01", "mercado-01")


def id_citacao(loja_id: str, periodo: str) -> str:
    """Identificador usado em fonte.trecho_id quando a resposta vem do resumo da loja."""
    return f"resumo:{loja_id}:{periodo}"


# O painel chama de luz_acesa o que o guia do grupo chama de luz_acesa_sem_necessidade.
_TIPO_DO_PAINEL = {"luz_acesa": "luz_acesa_sem_necessidade"}


def _tipo_pelo_equipamento(equipamento_id: str) -> str:
    """O resumo do painel não diz o tipo de cada equipamento. Lá, os ambientes iluminados têm
    id começando por 'luz' (luz-estoque, luz-salao); todo o resto é porta de refrigeração."""
    return "luz_acesa_sem_necessidade" if equipamento_id.startswith(("luz", "iluminacao")) else "porta_aberta"


def normalizar_resumo(dados: dict) -> dict:
    """Devolve o resumo no formato usado por este componente.

    Um resumo que já está nesse formato (linhas com custo_rs) volta como veio. Um resumo no
    formato do GET /summary do painel (linhas com total_rs, total_kwh e tempo_aberto_s) é
    convertido. Levanta KeyError ou TypeError se faltar campo.
    """
    linhas = dados.get("por_equipamento") or []
    if not linhas or "custo_rs" in linhas[0]:
        return dados
    por_equipamento = []
    for linha in linhas:
        tipo = linha.get("tipo") or _tipo_pelo_equipamento(linha["equipamento_id"])
        por_equipamento.append(
            {
                "equipamento_id": linha["equipamento_id"],
                "tipo": _TIPO_DO_PAINEL.get(tipo, tipo),
                "eventos": linha["eventos"],
                "duracao_total_s": linha["tempo_aberto_s"],
                "kwh": round(linha["total_kwh"], 2),
                "custo_rs": round(linha["total_rs"], 2),
            }
        )
    por_equipamento.sort(key=lambda linha: -linha["custo_rs"])
    return {
        "loja_id": dados.get("loja_id"),
        "periodo": dados.get("periodo"),
        "total_eventos": dados.get("eventos", sum(linha["eventos"] for linha in por_equipamento)),
        "total_kwh": round(dados["total_kwh"], 2),
        "total_custo_rs": round(dados["total_rs"], 2),
        "por_equipamento": por_equipamento,
    }


def ler_resumo(loja_id: str, periodo: str) -> dict | None:
    if loja_id not in LOJAS or not re.fullmatch(r"\d{4}-\d{2}", periodo or ""):
        return None
    painel = os.getenv("PAINEL_URL", "").rstrip("/")
    if painel:
        try:
            r = requests.get(f"{painel}/summary", params={"loja_id": loja_id, "periodo": periodo}, timeout=5)
            if r.ok:
                resumo = normalizar_resumo(r.json())
                # painel no ar e sem eventos no período: não há resumo, e o arquivo local não entra
                return resumo if resumo.get("por_equipamento") else None
        except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
            pass  # painel fora do ar ou resposta fora do formato: usa o arquivo local
    arquivo = config.DIR_DADOS / f"summary_{loja_id}_{periodo}.json"
    if arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))
    return None


def periodos_disponiveis(loja_id: str) -> list[str]:
    return sorted(p.stem.split("_")[-1] for p in config.DIR_DADOS.glob(f"summary_{loja_id}_*.json"))
