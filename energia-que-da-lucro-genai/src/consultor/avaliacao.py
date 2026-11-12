"""Correção automática, métricas da busca, calibração do limiar e placar.

Definições usadas em todo o projeto:

ACERTO
  caso respondível  -> o modelo respondeu (nao_consta=false) e a resposta contém os fatos do gabarito
  caso "não consta" -> o modelo recusou (nao_consta=true)

ALUCINAÇÃO (qualquer um dos quatro)
  a) respondeu um caso cujo gabarito é "não consta"
  b) a resposta afirma um fato que contradiz o gabarito: detectado pela lista nao_deve_conter
     do caso ou, no conjunto de teste, pela revisão manual (avaliacao/revisao_manual.json)
  c) citou uma fonte que não existe (trecho_id fora da base e que não é um resumo de loja)
  d) caso sobre uma loja respondido com dado que não bate com o resumo (dado de loja inventado)

O placar mostra as duas contagens: só a automática e a automática mais a revisão manual.

Um erro que não é alucinação é, por exemplo, recusar uma pergunta que a base responde,
ou responder de forma incompleta.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from . import busca, config
from .base import trecho_por_id
from .texto import normalizar

CATEGORIAS = ("factual", "calculo", "loja", "nao_consta")


@dataclass(frozen=True)
class Caso:
    id: str
    conjunto: str  # calibracao | teste
    categoria: str
    pergunta: str
    nao_consta: bool
    gabarito: str
    trechos_relevantes: tuple[str, ...]
    deve_conter: tuple[str, ...]
    nao_deve_conter: tuple[str, ...]


def carregar_casos(conjunto: str | None = None) -> list[Caso]:
    casos = []
    with open(config.DIR_AVALIACAO / "casos_teste.jsonl", encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            d = json.loads(linha)
            for campo in ("trechos_relevantes", "deve_conter", "nao_deve_conter"):
                d[campo] = tuple(d[campo])
            casos.append(Caso(**d))
    if conjunto:
        casos = [c for c in casos if c.conjunto == conjunto]
    return casos


# ------------------------------------------------------------ correção de uma resposta
@lru_cache(maxsize=1)
def carregar_revisao() -> dict:
    """Revisão manual das respostas do conjunto de teste (avaliacao/revisao_manual.json).

    A correção automática compara palavras; ela não percebe, por exemplo, um prazo inventado
    que não foi previsto no gabarito. A revisão registra esses casos, com a justificativa.
    """
    arquivo = config.DIR_AVALIACAO / "revisao_manual.json"
    if not arquivo.exists():
        return {}
    return json.loads(arquivo.read_text(encoding="utf-8"))


def _texto_para_correcao(texto: str) -> str:
    t = normalizar(texto)
    return re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", t)  # 1.200 -> 1200


def corrigir(caso: Caso, resposta: dict) -> dict:
    """resposta: dicionário de Resposta.como_dict()."""
    saida = resposta["saida"]
    respondeu = not saida["nao_consta"]
    texto = _texto_para_correcao(saida.get("recomendacao") or "")
    fonte_id = (saida.get("fonte") or {}).get("trecho_id")

    contem_gabarito = all(re.search(p, texto) for p in caso.deve_conter)
    contem_erro = any(re.search(p, texto) for p in caso.nao_deve_conter)

    if caso.nao_consta:
        acerto = not respondeu
    else:
        acerto = respondeu and contem_gabarito and not contem_erro

    fonte_existe = fonte_id is not None and (trecho_por_id(fonte_id) is not None or fonte_id.startswith("resumo:"))
    citacao_correta = respondeu and fonte_id in caso.trechos_relevantes

    motivos = []
    if caso.nao_consta and respondeu:
        motivos.append("respondeu o que não consta")
    if respondeu and contem_erro:
        motivos.append("fato errado")
    if respondeu and fonte_id is not None and not fonte_existe:
        motivos.append("fonte inexistente")
    if caso.categoria == "loja" and respondeu and not acerto:
        motivos.append("dado de loja não confere")

    acerto_automatico, alucinacao_automatica = acerto, bool(motivos)
    nota_revisao = None
    revisao = carregar_revisao().get(resposta["config"], {}).get(caso.id) if caso.conjunto == "teste" else None
    if revisao:
        nota_revisao = revisao["nota"]
        if "acerto" in revisao:
            acerto = revisao["acerto"]
        if revisao.get("alucinacao") and "fato errado (revisão manual)" not in motivos:
            motivos.append("fato errado (revisão manual)")

    return {
        "caso": caso.id,
        "categoria": caso.categoria,
        "config": resposta["config"],
        "acerto": acerto,
        "alucinacao": bool(motivos),
        "acerto_automatico": acerto_automatico,
        "alucinacao_automatica": alucinacao_automatica,
        "nota_revisao": nota_revisao,
        "motivos_alucinacao": motivos,
        "respondeu": respondeu,
        "recusa_correta": caso.nao_consta and not respondeu,
        "recusa_indevida": (not caso.nao_consta) and not respondeu,
        "citacao_correta": citacao_correta,
        "json_valido": resposta["json_valido"],
        "motivo": resposta["motivo"],
        "segundos": resposta["segundos"],
    }


# ------------------------------------------------------------ placar
def _pct(parte: int, total: int) -> float | None:
    return None if total == 0 else round(100 * parte / total, 1)


def resumir(correcoes: list[dict]) -> dict:
    """Uma linha do placar a partir das correções de uma configuração."""
    n = len(correcoes)
    respondiveis = [c for c in correcoes if c["categoria"] != "nao_consta"]
    nao_consta = [c for c in correcoes if c["categoria"] == "nao_consta"]
    respondidos = [c for c in respondiveis if c["respondeu"]]
    linha = {
        "casos": n,
        "acerto_%": _pct(sum(c["acerto"] for c in correcoes), n),
        "alucinacao_%": _pct(sum(c["alucinacao"] for c in correcoes), n),
        "alucinacao_automatica_%": _pct(sum(c["alucinacao_automatica"] for c in correcoes), n),
        "acerto_respondiveis_%": _pct(sum(c["acerto"] for c in respondiveis), len(respondiveis)),
        "recusa_correta_%": _pct(sum(c["recusa_correta"] for c in nao_consta), len(nao_consta)),
        "recusa_indevida_%": _pct(sum(c["recusa_indevida"] for c in respondiveis), len(respondiveis)),
        "citacao_correta_%": _pct(sum(c["citacao_correta"] for c in respondidos), len(respondidos)),
        "json_valido_%": _pct(sum(c["json_valido"] for c in correcoes), n),
        "segundos_medio": round(sum(c["segundos"] for c in correcoes) / n, 2) if n else None,
    }
    for categoria in CATEGORIAS:
        grupo = [c for c in correcoes if c["categoria"] == categoria]
        linha[f"acerto_{categoria}_%"] = _pct(sum(c["acerto"] for c in grupo), len(grupo))
    return linha


# ------------------------------------------------------------ busca: recall@k
def recall_da_busca(casos: list[Caso], funcao_busca, ks=(1, 3)) -> dict:
    """recall@k = fração dos casos em que algum trecho relevante aparece entre os k primeiros.

    Só entram casos respondíveis que têm trecho relevante na base (resumos de loja não são trechos).
    """
    avaliaveis = []
    for c in casos:
        relevantes = {t for t in c.trechos_relevantes if not t.startswith("resumo:")}
        if not c.nao_consta and relevantes:
            avaliaveis.append((c, relevantes))
    acertos = {k: 0 for k in ks}
    detalhe = []
    for caso, relevantes in avaliaveis:
        ids = [r.trecho.id for r in funcao_busca(caso.pergunta, max(ks))]
        posicao = next((i + 1 for i, t in enumerate(ids) if t in relevantes), None)
        for k in ks:
            if posicao is not None and posicao <= k:
                acertos[k] += 1
        detalhe.append({"caso": caso.id, "posicao_primeiro_relevante": posicao, "recuperados": ids})
    n = len(avaliaveis)
    return {"n": n, **{f"recall@{k}": round(acertos[k] / n, 3) for k in ks}, "detalhe": detalhe}


# ------------------------------------------------------------ limiar de recusa
def scores_top1(casos: list[Caso]) -> list[dict]:
    linhas = []
    for c in casos:
        r = busca.buscar_denso(c.pergunta, 1)
        linhas.append({"caso": c.id, "nao_consta": c.nao_consta, "categoria": c.categoria, "score": round(r[0].score, 4)})
    return linhas


def avaliar_limiar(linhas: list[dict], limiar: float) -> dict:
    """Trata 'score >= limiar' como 'a base deve ter a resposta'."""
    resp = [x for x in linhas if not x["nao_consta"]]
    nc = [x for x in linhas if x["nao_consta"]]
    mantidas = sum(x["score"] >= limiar for x in resp)
    barradas = sum(x["score"] < limiar for x in nc)
    sens = mantidas / len(resp) if resp else 0.0
    espec = barradas / len(nc) if nc else 0.0
    return {
        "limiar": round(limiar, 4),
        "respondiveis_mantidas_%": round(100 * sens, 1),
        "nao_consta_barradas_%": round(100 * espec, 1),
        "acuracia_balanceada": round((sens + espec) / 2, 3),
    }


def calibrar_limiar(linhas: list[dict], margem: float = 0.02) -> dict:
    """Escolhe o limiar no conjunto de calibração.

    Critério: o maior limiar que não barra nenhuma pergunta respondível da calibração,
    menos uma margem de segurança. Barrar uma pergunta legítima custa caro (o comerciante
    fica sem resposta), enquanto uma pergunta sem resposta que passa pelo limiar ainda é
    examinada pelo modelo e pelo verificador de citação.
    """
    # Perguntas sobre uma loja são respondidas pelo resumo da loja, não pela base:
    # não entram na calibração do limiar da busca.
    linhas = [x for x in linhas if x["categoria"] != "loja"]
    menor_respondivel = min(x["score"] for x in linhas if not x["nao_consta"])
    limiar = round(menor_respondivel - margem, 2)
    return {"limiar": limiar, "menor_score_respondivel": menor_respondivel, "margem": margem, **avaliar_limiar(linhas, limiar)}
