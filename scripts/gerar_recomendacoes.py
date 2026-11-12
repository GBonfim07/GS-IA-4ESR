"""Gera saida/recomendacoes.json: o arquivo que o painel carrega na tela de sugestões
e que a automação (RPA) usa no resumo por e-mail.

    python scripts/gerar_recomendacoes.py

O arquivo é uma lista de objetos no formato da seção 3 do guia do grupo:
    {"loja_id", "periodo", "nao_consta", "recomendacao", "fonte": {"titulo", "trecho_id"}}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor import config  # noqa: E402
from consultor.esquema import Recomendacao  # noqa: E402
from consultor.lote import recomendacoes_da_loja  # noqa: E402
from consultor.resumo import LOJAS, periodos_disponiveis  # noqa: E402


def main() -> None:
    recomendacoes = []
    for loja in LOJAS:
        for periodo in periodos_disponiveis(loja):
            for linha, r in recomendacoes_da_loja(loja, periodo):
                item = Recomendacao(loja_id=loja, periodo=periodo, **r.saida)  # valida o contrato
                recomendacoes.append(item.model_dump())
                estado = "não consta" if item.nao_consta else item.fonte.trecho_id
                print(f"{loja} {periodo} {linha['equipamento_id']:20} -> {estado}")
    config.DIR_SAIDA.mkdir(exist_ok=True)
    destino = config.DIR_SAIDA / "recomendacoes.json"
    destino.write_text(json.dumps(recomendacoes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(recomendacoes)} recomendações gravadas em {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
