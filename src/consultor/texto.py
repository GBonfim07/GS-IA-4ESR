"""Normalização de texto usada pela busca lexical e pela correção automática."""
from __future__ import annotations

import re
import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas e sem acentos. 'Refrigeração' vira 'refrigeracao'."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()


_STOPWORDS = {
    normalizar(p)
    for p in (
        "a o as os um uma uns umas de do da dos das em no na nos nas por para com sem que e ou se ao aos "
        "à às é ser são foi como qual quais quanto quanta quando onde meu minha seu sua isso esse essa este "
        "esta mais menos muito pelo pela pelos pelas eu me te ele ela nós vocês tem ter há devo posso deve pode"
    ).split()
}


def tokenizar(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if t not in _STOPWORDS and len(t) > 1]
