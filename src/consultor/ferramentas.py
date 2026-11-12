"""Ferramentas que o agente pode chamar. Cada resultado informa de onde veio (campo fonte)."""
from __future__ import annotations

import ast
import operator

from . import busca, config, resumo

ESPECIFICACAO = [
    {
        "type": "function",
        "function": {
            "name": "buscar_base",
            "description": "Procura trechos na base de conhecimento sobre eficiência energética, "
            "refrigeração, iluminação, tarifas, bandeiras, conservação de alimentos e regras do produto.",
            "parameters": {
                "type": "object",
                "properties": {"consulta": {"type": "string", "description": "O que procurar, em português."}},
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ler_resumo_loja",
            "description": "Lê o resumo de desperdício de uma loja em um mês: total em R$ e kWh e o "
            "detalhe por equipamento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "loja_id": {"type": "string", "enum": list(resumo.LOJAS)},
                    "periodo": {"type": "string", "description": "Mês no formato AAAA-MM, por exemplo 2026-10."},
                },
                "required": ["loja_id", "periodo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_custo_desperdicio",
            "description": "Aplica a fórmula do produto: custo = potencia_kw x fator_perda x horas x tarifa. "
            "Devolve kWh desperdiçados e custo em reais. Parâmetros omitidos usam o padrão do produto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "duracao_valor": {"type": "number", "description": "Tempo total de porta aberta."},
                    "unidade": {"type": "string", "enum": ["s", "min", "h"], "description": "Unidade do tempo."},
                    "potencia_kw": {"type": "number"},
                    "fator_perda": {"type": "number"},
                    "tarifa_rs_kwh": {"type": "number"},
                },
                "required": ["duracao_valor", "unidade"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculadora",
            "description": "Calcula uma expressão aritmética com + - * / e parênteses. Exemplo: 1200 * 0.07877",
            "parameters": {
                "type": "object",
                "properties": {"expressao": {"type": "string"}},
                "required": ["expressao"],
            },
        },
    },
]


def buscar_base(consulta: str) -> dict:
    resultados = busca.buscar(str(consulta))
    limiar = config.limiar_recusa()
    if not resultados or resultados[0].score < limiar:
        return {
            "resultados": [],
            "aviso": "Nenhum trecho relevante na base para esta consulta.",
            "_trechos": [],
            "_score_top1": resultados[0].score if resultados else 0.0,
        }
    return {
        "resultados": [
            {"trecho_id": r.trecho.id, "titulo": r.trecho.titulo, "texto": r.trecho.texto} for r in resultados
        ],
        "_trechos": [(r.trecho.id, round(r.score, 4)) for r in resultados],
        "_score_top1": resultados[0].score,
    }


def ler_resumo_loja(loja_id: str, periodo: str) -> dict:
    dados = resumo.ler_resumo(str(loja_id), str(periodo))
    if dados is None:
        disponiveis = resumo.periodos_disponiveis(str(loja_id))
        return {"erro": f"Não há resumo para {loja_id} em {periodo}.", "periodos_disponiveis": disponiveis}
    return {
        "resumo": dados,
        "fonte": {"trecho_id": resumo.id_citacao(loja_id, periodo), "titulo": "Resumo de desperdício da loja"},
    }


_SEGUNDOS = {"s": 1, "min": 60, "h": 3600}


def calcular_custo_desperdicio(
    duracao_valor: float,
    unidade: str = "s",
    potencia_kw: float | None = None,
    fator_perda: float | None = None,
    tarifa_rs_kwh: float | None = None,
) -> dict:
    if unidade not in _SEGUNDOS:
        return {"erro": "unidade deve ser s, min ou h"}
    duracao_s = float(duracao_valor) * _SEGUNDOS[unidade]
    if duracao_s <= 0:
        return {"erro": "a duração deve ser maior que zero"}
    potencia = config.POTENCIA_KW if potencia_kw is None else float(potencia_kw)
    fator = config.FATOR_PERDA if fator_perda is None else float(fator_perda)
    tarifa = config.TARIFA_RS_KWH if tarifa_rs_kwh is None else float(tarifa_rs_kwh)
    kwh = potencia * fator * duracao_s / 3600
    return {
        "duracao_s": duracao_s,
        "kwh_desperdicados": round(kwh, 4),
        "custo_rs": round(kwh * tarifa, 4),
        "parametros": {"potencia_kw": potencia, "fator_perda": fator, "tarifa_rs_kwh": tarifa},
        "fonte": {"trecho_id": "produto-contrato-01", "titulo": "Fórmula do custo estimado"},
    }


_OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _avaliar(no: ast.AST) -> float:
    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
        return float(no.value)
    if isinstance(no, ast.BinOp) and type(no.op) in _OPERADORES:
        return _OPERADORES[type(no.op)](_avaliar(no.left), _avaliar(no.right))
    if isinstance(no, ast.UnaryOp) and type(no.op) in _OPERADORES:
        return _OPERADORES[type(no.op)](_avaliar(no.operand))
    raise ValueError("expressão não permitida")


def calculadora(expressao: str) -> dict:
    """Aritmética segura: só números e + - * /. Não executa código."""
    texto = str(expressao).replace(",", ".").replace("×", "*").replace("x", "*")
    if len(texto) > 120:
        return {"erro": "expressão longa demais"}
    try:
        valor = _avaliar(ast.parse(texto, mode="eval").body)
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return {"erro": f"não consegui calcular: {e}"}
    return {"expressao": texto, "resultado": round(valor, 4)}


FUNCOES = {
    "buscar_base": buscar_base,
    "ler_resumo_loja": ler_resumo_loja,
    "calcular_custo_desperdicio": calcular_custo_desperdicio,
    "calculadora": calculadora,
}


def executar(nome: str, argumentos: dict) -> dict:
    if nome not in FUNCOES:
        return {"erro": f"ferramenta desconhecida: {nome}"}
    try:
        return FUNCOES[nome](**(argumentos or {}))
    except TypeError as e:
        return {"erro": f"argumentos inválidos para {nome}: {e}"}
