"""Busca na base: lexical (BM25) e densa (embeddings bge-m3 com similaridade de cosseno)."""
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from . import config, ollama
from .base import Trecho, carregar_trechos
from .texto import tokenizar

ARQ_VETORES = config.DIR_BASE / "indice" / "vetores.npy"
ARQ_IDS = config.DIR_BASE / "indice" / "ids.json"


@dataclass(frozen=True)
class Resultado:
    trecho: Trecho
    score: float


# ---------------------------------------------------------------- BM25
class IndiceBM25:
    """BM25 Okapi escrito à mão, para não depender de biblioteca externa."""

    def __init__(self, trechos: tuple[Trecho, ...], k1: float = 1.5, b: float = 0.75):
        self.trechos = trechos
        self.k1, self.b = k1, b
        self.docs = [tokenizar(t.texto_para_indice()) for t in trechos]
        self.tf = [Counter(d) for d in self.docs]
        self.tamanho_medio = sum(len(d) for d in self.docs) / len(self.docs)
        df = Counter(termo for d in self.docs for termo in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def buscar(self, consulta: str, k: int = config.TOP_K) -> list[Resultado]:
        termos = tokenizar(consulta)
        scores = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for termo in termos:
                if termo in tf:
                    f = tf[termo]
                    norma = 1 - self.b + self.b * len(self.docs[i]) / self.tamanho_medio
                    s += self.idf[termo] * f * (self.k1 + 1) / (f + self.k1 * norma)
            scores.append(s)
        ordem = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [Resultado(self.trechos[i], scores[i]) for i in ordem]


@lru_cache(maxsize=1)
def indice_bm25() -> IndiceBM25:
    return IndiceBM25(carregar_trechos())


# ---------------------------------------------------------------- Densa
def construir_indice_denso() -> np.ndarray:
    """Gera os embeddings de todos os trechos e grava em base/indice/."""
    trechos = carregar_trechos()
    vetores = np.array(ollama.embed([t.texto_para_indice() for t in trechos]), dtype=np.float32)
    vetores = vetores / np.linalg.norm(vetores, axis=1, keepdims=True)
    ARQ_VETORES.parent.mkdir(parents=True, exist_ok=True)
    np.save(ARQ_VETORES, vetores)
    ARQ_IDS.write_text(json.dumps([t.id for t in trechos]), encoding="utf-8")
    carregar_indice_denso.cache_clear()
    return vetores


@lru_cache(maxsize=1)
def carregar_indice_denso() -> np.ndarray:
    trechos = carregar_trechos()
    if ARQ_VETORES.exists() and ARQ_IDS.exists():
        ids = json.loads(ARQ_IDS.read_text(encoding="utf-8"))
        if ids == [t.id for t in trechos]:
            return np.load(ARQ_VETORES)
    return construir_indice_denso()  # índice ausente ou desatualizado


@lru_cache(maxsize=4096)
def _vetor_consulta(consulta: str) -> np.ndarray:
    v = np.array(ollama.embed([consulta])[0], dtype=np.float32)
    return v / np.linalg.norm(v)


def buscar_denso(consulta: str, k: int = config.TOP_K) -> list[Resultado]:
    vetores = carregar_indice_denso()
    scores = vetores @ _vetor_consulta(consulta)
    ordem = np.argsort(-scores)[:k]
    trechos = carregar_trechos()
    return [Resultado(trechos[i], float(scores[i])) for i in ordem]


def buscar(consulta: str, k: int = config.TOP_K) -> list[Resultado]:
    """Busca usada pelo RAG e pelo agente (densa)."""
    return buscar_denso(consulta, k)
