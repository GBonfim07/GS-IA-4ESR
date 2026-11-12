"""Configuração 3: agente com ferramentas (a especialização comparada ao RAG simples).

O agente parte da mesma busca do RAG simples e, a partir daí, o próprio modelo decide o que
fazer: buscar de novo com outras palavras, ler o resumo da loja ou fazer uma conta.
No fim, a resposta passa pelo mesmo verificador de citação do RAG.
"""
from __future__ import annotations

import json

from . import config, ferramentas, ollama, prompts
from .esquema import SCHEMA_FUNDAMENTADO, recusa
from .geracao import Resposta, gerar_json, saida_do_contrato, titulo_canonico

MAX_PASSOS = 6


def _publico(resultado: dict) -> dict:
    """Tira os campos internos (prefixo _) antes de mostrar o resultado ao modelo."""
    return {k: v for k, v in resultado.items() if not k.startswith("_")}


def responder_agente(pergunta: str) -> Resposta:
    limiar = config.limiar_recusa()
    mensagens: list[dict] = [
        {"role": "system", "content": prompts.SISTEMA_AGENTE},
        {"role": "user", "content": pergunta},
    ]
    passos: list[dict] = []
    trechos: dict[str, float] = {}
    permitidos: dict[str, str] = {}  # identificador citável -> título da fonte
    score_top1: float | None = None
    segundos = 0.0

    def registrar(nome: str, argumentos: dict, automatico: bool = False) -> None:
        nonlocal score_top1
        resultado = ferramentas.executar(nome, argumentos)
        if nome == "buscar_base":
            for trecho_id, score in resultado.get("_trechos", []):
                trechos[trecho_id] = max(score, trechos.get(trecho_id, 0.0))
                permitidos[trecho_id] = titulo_canonico(trecho_id) or ""
            s = resultado.get("_score_top1")
            if s is not None:
                score_top1 = max(s, score_top1 or 0.0)
        fonte = resultado.get("fonte")
        if fonte:
            permitidos[fonte["trecho_id"]] = titulo_canonico(fonte["trecho_id"]) or fonte["titulo"]
        passos.append({"ferramenta": nome, "argumentos": argumentos, "automatico": automatico, "resultado": _publico(resultado)})
        mensagens.append({"role": "tool", "tool_name": nome, "content": json.dumps(_publico(resultado), ensure_ascii=False)})

    # Passo 0: busca inicial obrigatória com a própria pergunta (a mesma do RAG simples).
    mensagens.append(
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "buscar_base", "arguments": {"consulta": pergunta}}}]}
    )
    registrar("buscar_base", {"consulta": pergunta}, automatico=True)

    # Passos seguintes: o modelo escolhe as ferramentas.
    for _ in range(MAX_PASSOS):
        r = ollama.chat(mensagens, ferramentas=ferramentas.ESPECIFICACAO)
        segundos += r["segundos"]
        mensagem = r["mensagem"]
        chamadas = mensagem.get("tool_calls") or []
        if not chamadas:
            break
        mensagens.append(mensagem)
        for chamada in chamadas:
            argumentos = chamada["function"].get("arguments") or {}
            if isinstance(argumentos, str):
                try:
                    argumentos = json.loads(argumentos)
                except json.JSONDecodeError:
                    argumentos = {}
            registrar(chamada["function"]["name"], argumentos)

    comum = dict(
        trechos=sorted(trechos.items(), key=lambda x: -x[1]),
        score_top1=None if score_top1 is None else round(score_top1, 4),
        limiar=limiar,
        passos=passos,
    )

    if not permitidos:
        # Nenhuma ferramenta trouxe evidência citável: recusa sem pedir texto ao modelo.
        return Resposta("agente", recusa(), "recusa_sem_evidencia", True, segundos, **comum)

    # Síntese: o mesmo pedido fundamentado do RAG simples, agora com tudo o que o agente reuniu.
    mensagens = [
        {"role": "system", "content": prompts.SISTEMA_SINTESE_AGENTE},
        {"role": "user", "content": prompts.bloco_agente(pergunta, list(trechos), passos)},
    ]
    saida, valido, bruto, s = gerar_json(mensagens, SCHEMA_FUNDAMENTADO, prompts.FORMATO)
    segundos += s
    if saida is None:
        return Resposta("agente", recusa(), "json_invalido", False, segundos, bruto=bruto, **comum)
    if saida.nao_consta:
        return Resposta("agente", recusa(), "recusa_modelo", valido, segundos, bruto=bruto, **comum)
    if saida.fonte is None or saida.fonte.trecho_id not in permitidos:
        return Resposta("agente", recusa(), "recusa_citacao_invalida", valido, segundos, bruto=bruto, **comum)

    titulo = permitidos[saida.fonte.trecho_id] or None
    return Resposta(
        "agente", saida_do_contrato(saida, titulo), "resposta", valido, segundos, evidencia=saida.evidencia, bruto=bruto, **comum
    )
