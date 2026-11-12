"""Configuração central. Tudo que muda entre máquinas vem de variável de ambiente."""
from __future__ import annotations

import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _carregar_env(arquivo: Path) -> None:
    """Lê um arquivo .env (NOME=valor por linha). O que já está no ambiente tem prioridade."""
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        if valor.strip():
            os.environ.setdefault(nome.strip(), valor.strip().strip("'\""))


_carregar_env(RAIZ / ".env")

DIR_BASE = RAIZ / "base"
DIR_AVALIACAO = RAIZ / "avaliacao"
DIR_DADOS = RAIZ / "dados"
DIR_SAIDA = RAIZ / "saida"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELO_LLM = os.getenv("MODELO_LLM", "qwen2.5:7b")
MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "bge-m3")

# Geração determinística: mesma pergunta, mesma resposta.
OPCOES_LLM = {"temperature": 0, "seed": 42, "num_ctx": 8192}

TOP_K = 3

# Limiar de recusa da busca (similaridade de cosseno do melhor trecho).
# O valor é calibrado em notebooks/01_base_e_busca.ipynb e gravado em avaliacao/limiar.json.
LIMIAR_PADRAO = 0.50
ARQ_LIMIAR = DIR_AVALIACAO / "limiar.json"

# Parâmetros provisórios da fórmula de custo (guia do grupo, seção 3).
TARIFA_RS_KWH = 0.90
POTENCIA_KW = 0.50
FATOR_PERDA = 0.30

# API
API_KEY = os.getenv("CONSULTOR_API_KEY", "")  # vazio = sem autenticação (uso local)
MAX_CARACTERES_PERGUNTA = 600


def limiar_recusa() -> float:
    """Lê o limiar calibrado; cai no padrão se ainda não foi calibrado."""
    if os.getenv("LIMIAR_RECUSA"):
        return float(os.environ["LIMIAR_RECUSA"])
    if ARQ_LIMIAR.exists():
        return float(json.loads(ARQ_LIMIAR.read_text(encoding="utf-8"))["limiar"])
    return LIMIAR_PADRAO
