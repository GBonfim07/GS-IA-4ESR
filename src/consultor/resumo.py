"""Resumo de desperdício de uma loja, no formato do GET /summary do painel.

Por padrão lê os arquivos simulados em dados/. Se a variável PAINEL_URL estiver definida,
tenta primeiro a API do painel e cai no arquivo se ela estiver fora do ar.
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


def ler_resumo(loja_id: str, periodo: str) -> dict | None:
    if loja_id not in LOJAS or not re.fullmatch(r"\d{4}-\d{2}", periodo or ""):
        return None
    painel = os.getenv("PAINEL_URL", "").rstrip("/")
    if painel:
        try:
            r = requests.get(f"{painel}/summary", params={"loja_id": loja_id, "periodo": periodo}, timeout=5)
            if r.ok:
                return r.json()
        except requests.RequestException:
            pass  # painel fora do ar: usa o arquivo local
    arquivo = config.DIR_DADOS / f"summary_{loja_id}_{periodo}.json"
    if arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))
    return None


def periodos_disponiveis(loja_id: str) -> list[str]:
    return sorted(p.stem.split("_")[-1] for p in config.DIR_DADOS.glob(f"summary_{loja_id}_*.json"))
