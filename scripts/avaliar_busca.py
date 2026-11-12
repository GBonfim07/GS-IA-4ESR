"""Constrói o índice, mede recall@1 e recall@3 e calibra o limiar de recusa.

    python scripts/avaliar_busca.py

Saídas:
    base/indice/            embeddings dos trechos
    avaliacao/busca.json    recall das duas buscas e scores usados na calibração
    avaliacao/limiar.json   limiar escolhido (lido pelo RAG e pelo agente)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor import avaliacao, busca, config  # noqa: E402


def main() -> dict:
    busca.construir_indice_denso()
    buscas = {"bm25": lambda q, k: busca.indice_bm25().buscar(q, k), "denso": busca.buscar_denso}
    recall = {}
    for nome, funcao in buscas.items():
        for conjunto in ("calibracao", "teste"):
            r = avaliacao.recall_da_busca(avaliacao.carregar_casos(conjunto), funcao)
            recall[f"{nome}_{conjunto}"] = r
            print(f"{nome:6} {conjunto:11} n={r['n']:2}  recall@1={r['recall@1']:.3f}  recall@3={r['recall@3']:.3f}")

    scores_cal = avaliacao.scores_top1(avaliacao.carregar_casos("calibracao"))
    escolha = avaliacao.calibrar_limiar(scores_cal)
    scores_teste = avaliacao.scores_top1(avaliacao.carregar_casos("teste"))
    sem_loja = [x for x in scores_teste if x["categoria"] != "loja"]
    no_teste = avaliacao.avaliar_limiar(sem_loja, escolha["limiar"])
    print("limiar escolhido na calibração:", escolha)
    print("efeito no conjunto de teste:   ", no_teste)

    (config.DIR_AVALIACAO / "limiar.json").write_text(
        json.dumps({"limiar": escolha["limiar"], "calibracao": escolha, "teste": no_teste}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    saida = {"recall": recall, "scores_calibracao": scores_cal, "scores_teste": scores_teste, "limiar": escolha, "limiar_no_teste": no_teste}
    (config.DIR_AVALIACAO / "busca.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida


if __name__ == "__main__":
    main()
