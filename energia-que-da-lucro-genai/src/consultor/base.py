"""Leitura da base de conhecimento (trechos e fontes)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from . import config


@dataclass(frozen=True)
class Trecho:
    id: str
    doc_id: str
    titulo: str
    localizador: str
    texto: str

    def texto_para_indice(self) -> str:
        return f"{self.titulo}\n{self.texto}"


@lru_cache(maxsize=1)
def carregar_trechos() -> tuple[Trecho, ...]:
    trechos = []
    with open(config.DIR_BASE / "trechos.jsonl", encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                trechos.append(Trecho(**json.loads(linha)))
    ids = [t.id for t in trechos]
    if len(ids) != len(set(ids)):
        raise ValueError("Há ids de trecho repetidos em base/trechos.jsonl")
    return tuple(trechos)


@lru_cache(maxsize=1)
def carregar_fontes() -> dict[str, dict]:
    fontes = json.loads((config.DIR_BASE / "fontes.json").read_text(encoding="utf-8"))
    return {f["doc_id"]: f for f in fontes}


def trecho_por_id(trecho_id: str) -> Trecho | None:
    return next((t for t in carregar_trechos() if t.id == trecho_id), None)


def tabela_da_base() -> list[dict]:
    """Uma linha por fonte: órgão, título, formato, licença e número de trechos."""
    contagem: dict[str, int] = {}
    for t in carregar_trechos():
        contagem[t.doc_id] = contagem.get(t.doc_id, 0) + 1
    linhas = []
    for doc_id, f in carregar_fontes().items():
        linhas.append(
            {
                "doc_id": doc_id,
                "orgao": f["orgao"],
                "titulo": f["titulo"],
                "formato": f["formato"],
                "licenca": f["licenca"],
                "tipo_trecho": f["tipo_trecho"],
                "n_trechos": contagem.get(doc_id, 0),
                "url": f["url"],
            }
        )
    return linhas
