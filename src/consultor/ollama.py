"""Cliente mínimo da API HTTP do Ollama (LLM e embeddings rodando na própria máquina)."""
from __future__ import annotations

import time

import requests

from . import config


class OllamaIndisponivel(RuntimeError):
    pass


def _post(caminho: str, corpo: dict, timeout: int = 300) -> dict:
    ultimo_erro: Exception | None = None
    for tentativa in range(3):
        try:
            r = requests.post(f"{config.OLLAMA_URL}{caminho}", json=corpo, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:  # tenta de novo com espera crescente
            ultimo_erro = e
            time.sleep(1.5 * (tentativa + 1))
    raise OllamaIndisponivel(
        f"Não consegui falar com o Ollama em {config.OLLAMA_URL}. "
        f"Confira se ele está aberto e se os modelos foram baixados. Erro: {ultimo_erro}"
    )


def embed(textos: list[str]) -> list[list[float]]:
    resposta = _post("/api/embed", {"model": config.MODELO_EMBEDDING, "input": textos})
    return resposta["embeddings"]


def chat(mensagens: list[dict], formato: dict | None = None, ferramentas: list[dict] | None = None) -> dict:
    """Uma chamada ao modelo. Devolve a mensagem do assistente e a duração em segundos."""
    corpo: dict = {
        "model": config.MODELO_LLM,
        "messages": mensagens,
        "stream": False,
        "options": config.OPCOES_LLM,
    }
    if formato is not None:
        corpo["format"] = formato
    if ferramentas:
        corpo["tools"] = ferramentas
    inicio = time.perf_counter()
    resposta = _post("/api/chat", corpo)
    return {"mensagem": resposta["message"], "segundos": time.perf_counter() - inicio}


def disponivel() -> bool:
    try:
        return requests.get(f"{config.OLLAMA_URL}/api/version", timeout=3).ok
    except requests.RequestException:
        return False
