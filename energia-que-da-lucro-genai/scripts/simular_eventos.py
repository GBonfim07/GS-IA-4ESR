"""Gera eventos de desperdício simulados e os resumos por loja e mês.

Os eventos seguem o contrato da seção 3 do guia do grupo. Os resumos seguem o que o
GET /summary do painel promete: total em R$ e kWh no período e detalhe por equipamento.

A geração é determinística (semente fixa): rodar de novo produz os mesmos arquivos.

    python scripts/simular_eventos.py
"""
from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor import config  # noqa: E402

BRT = timezone(timedelta(hours=-3))
SEMENTE = 42

# Horário de funcionamento (guia, seção 3).
LOJAS = {"padaria-01": (6, 20), "mercado-01": (7, 21)}

# Para cada equipamento: eventos por dia (média) e duração típica em segundos.
# Os valores foram escolhidos para dar a cada loja um "vilão" claro, que a IA precisa achar.
PERFIL = {
    "padaria-01": {
        "expositor-1": {"tipo": "porta_aberta", "por_dia": 5, "duracao": (70, 240)},
        "expositor-2": {"tipo": "porta_aberta", "por_dia": 14, "duracao": (90, 600)},  # vilão
        "freezer-1": {"tipo": "porta_aberta", "por_dia": 3, "duracao": (65, 200)},
        "iluminacao-salao": {"tipo": "luz_acesa_sem_necessidade", "por_dia": 0.4, "duracao": (900, 3600)},
    },
    "mercado-01": {
        "expositor-1": {"tipo": "porta_aberta", "por_dia": 6, "duracao": (70, 260)},
        "expositor-2": {"tipo": "porta_aberta", "por_dia": 5, "duracao": (70, 240)},
        "expositor-3": {"tipo": "porta_aberta", "por_dia": 4, "duracao": (65, 220)},
        "freezer-1": {"tipo": "porta_aberta", "por_dia": 4, "duracao": (65, 240)},
        "freezer-2": {"tipo": "porta_aberta", "por_dia": 9, "duracao": (80, 420)},
        "iluminacao-salao": {"tipo": "luz_acesa_sem_necessidade", "por_dia": 0.3, "duracao": (900, 2700)},
        "iluminacao-estoque": {"tipo": "luz_acesa_sem_necessidade", "por_dia": 2.5, "duracao": (1800, 7200)},  # vilão
    },
}

# Potência e fator de perda por equipamento.
# Refrigeração: valores provisórios do guia (0,50 kW e 0,30).
# Iluminação: o guia não define; adotamos uma premissa de simulação (luz acesa sem ninguém = 100% de perda).
POTENCIA_KW = {"iluminacao-salao": 0.40, "iluminacao-estoque": 0.12}
FATOR_PERDA = {"iluminacao-salao": 1.0, "iluminacao-estoque": 1.0}

PERIODOS = {"2026-10": 31, "2026-11": 9}  # novembro vai só até o dia 9 (mês em andamento)


def custo(equipamento: str, duracao_s: int) -> tuple[float, float]:
    potencia = POTENCIA_KW.get(equipamento, config.POTENCIA_KW)
    fator = FATOR_PERDA.get(equipamento, config.FATOR_PERDA)
    kwh = potencia * fator * duracao_s / 3600
    return kwh, kwh * config.TARIFA_RS_KWH


def gerar() -> None:
    rnd = random.Random(SEMENTE)
    config.DIR_DADOS.mkdir(exist_ok=True)
    for periodo, dias in PERIODOS.items():
        ano, mes = map(int, periodo.split("-"))
        for loja, (abre, fecha) in LOJAS.items():
            eventos = []
            for equipamento, p in PERFIL[loja].items():
                for dia in range(1, dias + 1):
                    quantidade = int(p["por_dia"]) + (1 if rnd.random() < p["por_dia"] % 1 else 0)
                    quantidade = max(0, quantidade + rnd.choice([-1, 0, 0, 1]))
                    for _ in range(quantidade):
                        if p["tipo"] == "porta_aberta":
                            hora = rnd.uniform(abre, fecha)  # porta aberta acontece com a loja aberta
                        else:
                            hora = rnd.choice([rnd.uniform(fecha, 23.5), rnd.uniform(abre, fecha)])
                        inicio = datetime(ano, mes, dia, tzinfo=BRT) + timedelta(hours=hora)
                        duracao_s = rnd.randint(*p["duracao"])
                        _, reais = custo(equipamento, duracao_s)
                        eventos.append(
                            {
                                "id": str(uuid.UUID(int=rnd.getrandbits(128), version=4)),
                                "loja_id": loja,
                                "equipamento_id": equipamento,
                                "tipo": p["tipo"],
                                "origem": "simulador",
                                "inicio": inicio.replace(microsecond=0).isoformat(),
                                "duracao_s": duracao_s,
                                "custo_estimado_rs": round(reais, 4),
                            }
                        )
            eventos.sort(key=lambda e: e["inicio"])
            (config.DIR_DADOS / f"eventos_{loja}_{periodo}.json").write_text(
                json.dumps(eventos, ensure_ascii=False, indent=1), encoding="utf-8"
            )

            por_equipamento = {}
            for e in eventos:
                linha = por_equipamento.setdefault(
                    e["equipamento_id"],
                    {"equipamento_id": e["equipamento_id"], "tipo": e["tipo"], "eventos": 0, "duracao_total_s": 0, "kwh": 0.0, "custo_rs": 0.0},
                )
                kwh, reais = custo(e["equipamento_id"], e["duracao_s"])
                linha["eventos"] += 1
                linha["duracao_total_s"] += e["duracao_s"]
                linha["kwh"] += kwh
                linha["custo_rs"] += reais
            linhas = sorted(por_equipamento.values(), key=lambda x: -x["custo_rs"])
            for linha in linhas:
                linha["kwh"] = round(linha["kwh"], 2)
                linha["custo_rs"] = round(linha["custo_rs"], 2)
            resumo = {
                "loja_id": loja,
                "periodo": periodo,
                "total_eventos": len(eventos),
                "total_kwh": round(sum(x["kwh"] for x in linhas), 2),
                "total_custo_rs": round(sum(x["custo_rs"] for x in linhas), 2),
                "por_equipamento": linhas,
            }
            (config.DIR_DADOS / f"summary_{loja}_{periodo}.json").write_text(
                json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"{loja} {periodo}: {len(eventos)} eventos, {resumo['total_kwh']} kWh, R$ {resumo['total_custo_rs']}")


if __name__ == "__main__":
    gerar()
