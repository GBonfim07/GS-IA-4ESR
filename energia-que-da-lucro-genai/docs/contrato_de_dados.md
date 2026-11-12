# Contrato de dados usado por este componente

Extraído do guia do grupo (versão 1, 10/11/2026, seção 3). É a origem dos trechos `produto-contrato-*` da base.

## Entrada: resumo da loja (formato do `GET /summary?loja_id=&periodo=` do painel)

O guia define o conteúdo ("total em R$ e kWh no período, por equipamento"), mas não os nomes dos campos.
Este componente usa o formato abaixo, gerado por `scripts/simular_eventos.py`. Se o painel publicar outro
formato, basta ajustar `src/consultor/resumo.py`.

```json
{
  "loja_id": "padaria-01",
  "periodo": "2026-10",
  "total_eventos": 698,
  "total_kwh": 11.9,
  "total_custo_rs": 10.72,
  "por_equipamento": [
    {"equipamento_id": "expositor-2", "tipo": "porta_aberta", "eventos": 431,
     "duracao_total_s": 147336, "kwh": 6.14, "custo_rs": 5.53}
  ]
}
```

## Saída: recomendação (seção 3 do guia)

```json
{
  "loja_id": "padaria-01",
  "periodo": "2026-10",
  "nao_consta": false,
  "recomendacao": "texto curto e prático",
  "fonte": {"titulo": "nome do documento", "trecho_id": "id do trecho na base"}
}
```

Quando a base não tem a resposta: `"nao_consta": true`, `"recomendacao": ""` e `"fonte": null`.

`saida/recomendacoes.json` é uma lista desses objetos, com até três recomendações por loja e mês
(uma para cada equipamento que mais desperdiçou).

## Fórmula do custo estimado

```
custo_estimado_rs = potencia_kw × fator_perda × (duracao_s / 3600) × tarifa_rs_kwh
```

Valores provisórios do guia: `tarifa_rs_kwh = 0,90`, `potencia_kw = 0,50` (expositor ou freezer),
`fator_perda = 0,30`, alerta com mais de 60 s de porta aberta. O guia avisa que esses números são
estimativas iniciais, sem fonte.

Premissa adicional da simulação (não está no guia): para eventos `luz_acesa_sem_necessidade` usamos
`iluminacao-salao = 0,40 kW`, `iluminacao-estoque = 0,12 kW` e `fator_perda = 1,0`.

## Observação sobre o exemplo do guia

O evento de exemplo do guia traz `duracao_s: 95` e `custo_estimado_rs: 0.04`. Pela fórmula, 95 s custam
R$ 0,0036. Este componente segue a fórmula.
