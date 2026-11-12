"""Contrato de saída (guia do grupo, seção 3) e validação."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class Fonte(BaseModel):
    titulo: str = Field(min_length=1)
    trecho_id: str = Field(min_length=1)


class SaidaLLM(BaseModel):
    """O que o modelo precisa devolver. loja_id e periodo são preenchidos pelo código.

    evidencia existe só no RAG e no agente: é a frase da base que sustenta a resposta.
    Ela obriga o modelo a localizar o dado antes de decidir se responde ou recusa.
    """

    evidencia: str = ""
    nao_consta: bool
    recomendacao: str
    fonte: Fonte | None

    @model_validator(mode="after")
    def coerencia(self):
        if not self.nao_consta and not self.recomendacao.strip():
            raise ValueError("resposta sem recomendação e sem nao_consta")
        return self


class Recomendacao(BaseModel):
    """Formato entregue ao painel e à automação (RPA)."""

    loja_id: str | None = None
    periodo: str | None = None
    nao_consta: bool
    recomendacao: str
    fonte: Fonte | None


_FONTE = {
    "anyOf": [
        {
            "type": "object",
            "properties": {"titulo": {"type": "string"}, "trecho_id": {"type": "string"}},
            "required": ["titulo", "trecho_id"],
        },
        {"type": "null"},
    ]
}

# JSON Schemas passados ao Ollama para decodificação restrita.
SCHEMA_PURO = {
    "type": "object",
    "properties": {"nao_consta": {"type": "boolean"}, "recomendacao": {"type": "string"}, "fonte": _FONTE},
    "required": ["nao_consta", "recomendacao", "fonte"],
}

SCHEMA_FUNDAMENTADO = {
    "type": "object",
    "properties": {
        "evidencia": {"type": "string"},
        "nao_consta": {"type": "boolean"},
        "recomendacao": {"type": "string"},
        "fonte": _FONTE,
    },
    "required": ["evidencia", "nao_consta", "recomendacao", "fonte"],
}


def recusa() -> dict:
    return {"nao_consta": True, "recomendacao": "", "fonte": None}
