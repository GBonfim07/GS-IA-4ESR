"""Roda os casos de teste nas três configurações e grava resultados e placar.

    python scripts/avaliar.py                    # conjunto de teste, três configurações
    python scripts/avaliar.py --conjunto calibracao
    python scripts/avaliar.py --config rag       # só uma configuração
    python scripts/avaliar.py --recorrigir       # não chama a LLM: corrige de novo as respostas já gravadas

Saídas em avaliacao/:
    resultados/<conjunto>_<config>.jsonl   resposta completa e correção de cada caso
    placar_<conjunto>.csv e placar_<conjunto>.md
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor import avaliacao, config, consultor  # noqa: E402

NOMES = {"puro": "1. Modelo puro", "rag": "2. RAG simples", "agente": "3. Agente com ferramentas"}

COLUNAS_MD = [
    ("acerto_%", "Acerto"),
    ("alucinacao_%", "Alucinação (com revisão manual)"),
    ("alucinacao_automatica_%", "Alucinação (só automática)"),
    ("recusa_correta_%", "Recusa correta (não consta)"),
    ("recusa_indevida_%", "Recusa indevida"),
    ("citacao_correta_%", "Citação correta"),
    ("json_valido_%", "JSON válido"),
    ("segundos_medio", "Tempo médio (s)"),
]


def _arquivo(conjunto: str, nome: str) -> Path:
    return config.DIR_AVALIACAO / "resultados" / f"{conjunto}_{nome}.jsonl"


def rodar(conjunto: str, configuracoes: list[str], recorrigir: bool = False) -> dict:
    casos = avaliacao.carregar_casos(conjunto)
    (config.DIR_AVALIACAO / "resultados").mkdir(parents=True, exist_ok=True)
    placar = {}
    for nome in configuracoes:
        gravadas = {}
        if recorrigir:
            with open(_arquivo(conjunto, nome), encoding="utf-8") as f:
                gravadas = {json.loads(l)["caso"]: json.loads(l)["resposta"] for l in f if l.strip()}
        registros, correcoes = [], []
        for i, caso in enumerate(casos, 1):
            resposta = gravadas[caso.id] if recorrigir else consultor.responder(caso.pergunta, nome).como_dict()
            correcao = avaliacao.corrigir(caso, resposta)
            correcoes.append(correcao)
            registros.append({"caso": caso.id, "pergunta": caso.pergunta, "gabarito": caso.gabarito, "resposta": resposta, "correcao": correcao})
            if not recorrigir:
                marca = "ok " if correcao["acerto"] else ("ALU" if correcao["alucinacao"] else "err")
                print(f"[{nome:6}] {i:2}/{len(casos)} {caso.id} {marca} {resposta['motivo']}", flush=True)
        with open(_arquivo(conjunto, nome), "w", encoding="utf-8") as f:
            for registro in registros:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        placar[nome] = avaliacao.resumir(correcoes)
    return placar


def gravar_placar(conjunto: str, placar: dict) -> None:
    chaves = list(next(iter(placar.values())).keys())
    with open(config.DIR_AVALIACAO / f"placar_{conjunto}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["configuracao", *chaves])
        for nome, linha in placar.items():
            w.writerow([nome, *[linha[k] for k in chaves]])

    def fmt(chave, valor):
        if valor is None:
            return "n/a"
        return f"{valor:.2f}" if chave == "segundos_medio" else f"{valor:.1f}%"

    linhas = [
        f"# Placar ({conjunto})",
        "",
        f"Modelo: `{config.MODELO_LLM}` · embeddings: `{config.MODELO_EMBEDDING}` · limiar de recusa: {config.limiar_recusa()} · "
        f"{next(iter(placar.values()))['casos']} casos",
        "",
        "| Configuração | " + " | ".join(t for _, t in COLUNAS_MD) + " |",
        "|---|" + "---:|" * len(COLUNAS_MD),
    ]
    for nome, linha in placar.items():
        linhas.append(f"| {NOMES[nome]} | " + " | ".join(fmt(k, linha[k]) for k, _ in COLUNAS_MD) + " |")
    linhas += ["", "## Acerto por categoria", "", "| Configuração | Factual | Cálculo | Loja | Não consta |", "|---|---:|---:|---:|---:|"]
    for nome, linha in placar.items():
        linhas.append(
            f"| {NOMES[nome]} | " + " | ".join(fmt("x", linha[f"acerto_{c}_%"]) for c in avaliacao.CATEGORIAS) + " |"
        )
    (config.DIR_AVALIACAO / f"placar_{conjunto}.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--conjunto", default="teste", choices=["teste", "calibracao"])
    p.add_argument("--config", action="append", choices=list(consultor.CONFIGURACOES))
    p.add_argument("--recorrigir", action="store_true", help="corrige de novo as respostas gravadas, sem chamar a LLM")
    args = p.parse_args()
    configuracoes = args.config or list(consultor.CONFIGURACOES)
    resultado = rodar(args.conjunto, configuracoes, args.recorrigir)
    if len(configuracoes) == len(consultor.CONFIGURACOES):
        gravar_placar(args.conjunto, resultado)
    else:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
