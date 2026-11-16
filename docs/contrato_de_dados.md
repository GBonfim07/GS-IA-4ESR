# Contrato de dados usado por este componente

Extraído do guia do grupo (versão 1, 10/11/2026, seção 3). É a origem dos trechos `produto-contrato-*` da base.

## Entrada: resumo da loja

O guia define o conteúdo do `GET /summary?loja_id=&periodo=` do painel ("total em R$ e kWh no período,
por equipamento"), mas não os nomes dos campos. Este componente usa o formato abaixo, gerado por
`scripts/simular_eventos.py`. O painel publicado usa outros nomes; a conversão está na seção
[O formato do painel publicado](#o-formato-do-painel-publicado).

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

## O formato do painel publicado

O painel do comerciante é a entrega de Secure DevOps ([repositório](https://github.com/Natan-TI/devops-energia)).
Esta seção foi escrita lendo o código dele em 15/11/2026 (`app/servico.py`, `app/schemas.py`,
`app/templates/sugestoes.html` e `simulador/simulador.py`). O painel roda em um laboratório da AWS que
só fica ligado durante as sessões, e estava desligado nessa data.

### Recomendações: mesmo formato

O painel lê `dados/recomendacoes.json` e mostra cada item na tela Sugestões (`/sugestoes`) e em
`GET /recommendations?loja_id=`. Os campos que ele usa são os mesmos da seção
[Saída](#saída-recomendação-seção-3-do-guia): `loja_id`, `periodo`, `nao_consta`, `recomendacao`,
`fonte.titulo` e `fonte.trecho_id`. O `saida/recomendacoes.json` deste repositório pode ser copiado
para lá sem conversão.

### Resumo da loja: outros nomes de campos

Corpo do `GET /summary?loja_id=&periodo=AAAA-MM` do painel:

```json
{
  "loja_id": "padaria-01",
  "periodo": "2026-11",
  "eventos": 735,
  "total_rs": 14.1996,
  "total_kwh": 17.997,
  "tempo_aberto_s": 257340,
  "por_equipamento": [
    {"equipamento_id": "expositor-bebidas", "eventos": 520, "total_rs": 9.8765,
     "total_kwh": 12.5178, "tempo_aberto_s": 70740}
  ],
  "por_tipo": [{"tipo": "porta_aberta", "eventos": 690, "total_rs": 10.7947, "total_kwh": 13.6815, "tempo_s": 113490}],
  "por_dia": [{"dia": "2026-11-01", "eventos": 735, "total_rs": 14.1996, "total_kwh": 17.997}]
}
```

Os números desse exemplo foram montados à mão com os parâmetros de custo do painel; não vieram do
painel no ar. É a mesma amostra usada em `tests/test_consultor.py`.

`normalizar_resumo`, em `src/consultor/resumo.py`, converte esse corpo para o formato da seção
[Entrada](#entrada-resumo-da-loja):

| Campo do painel | Campo neste componente | Observação |
|---|---|---|
| `eventos` (no topo) | `total_eventos` | |
| `total_rs` (no topo) | `total_custo_rs` | arredondado para 2 casas |
| `total_kwh` (no topo) | `total_kwh` | arredondado para 2 casas |
| `por_equipamento[].total_rs` | `por_equipamento[].custo_rs` | arredondado para 2 casas, que é o valor conferido no texto da recomendação |
| `por_equipamento[].total_kwh` | `por_equipamento[].kwh` | arredondado para 2 casas |
| `por_equipamento[].tempo_aberto_s` | `por_equipamento[].duracao_total_s` | |
| não existe por equipamento | `por_equipamento[].tipo` | deduzido do nome: `luz...` ou `iluminacao...` vira `luz_acesa_sem_necessidade`; o resto, `porta_aberta` |
| `por_tipo`, `por_dia` | não usados | |

Se o painel responder fora desse formato ou estiver fora do ar, vale o arquivo de `dados/`. Se
responder sem nenhum equipamento no período, não há resumo.

### O que continua diferente

| | Neste repositório (guia, versão 1) | Painel publicado |
|---|---|---|
| Equipamentos | `expositor-1`, `expositor-2`, `freezer-1`, `iluminacao-salao`, `iluminacao-estoque` | `expositor-bebidas`, `expositor-frios`, `freezer-sorvetes`, `luz-salao`, `luz-estoque` e outros |
| Tipo do evento de luz | `luz_acesa_sem_necessidade` | `luz_acesa` |
| Origem do evento do robô | `maker` | `robo` |
| Tarifa | R$ 0,90/kWh, provisória | R$ 0,789/kWh (Enel SP, B3 convencional, sem impostos, conforme o README do painel) |
| Potência | 0,50 kW para expositor ou freezer | 0,91 kW, 0,36 kW ou 0,14 kW, conforme o equipamento |
| Fator de perda da porta aberta | 0,30 | 0,70 |

Os nomes não atrapalham a leitura: o conversor aceita os do painel. Os valores de custo importam para
as perguntas de cálculo: a ferramenta `calcular_custo_desperdicio` e o trecho `produto-contrato-02`
usam os valores provisórios do guia, e por isso uma conta feita pelo Consultor com os valores padrão
não bate com o valor que o painel mostra. Trocar esses valores muda o gabarito das perguntas de
cálculo e exige refazer o placar; ficou como próximo passo.
