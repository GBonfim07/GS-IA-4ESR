# Dados simulados das lojas

O professor liberou dados simulados, desde que a geração seja documentada. Estes arquivos substituem a
API do painel enquanto ela não está no ar.

| Arquivo | Conteúdo |
|---|---|
| `eventos_<loja>_<AAAA-MM>.json` | eventos de desperdício no contrato da seção 3 do guia (`origem: "simulador"`) |
| `summary_<loja>_<AAAA-MM>.json` | resumo do período: total em R$ e kWh e detalhe por equipamento (o que o `GET /summary` do painel promete) |

Lojas: `padaria-01` e `mercado-01`. Períodos: `2026-10` (mês fechado) e `2026-11` (dias 1 a 9, mês em andamento).

## Como foram gerados

`python scripts/simular_eventos.py`, com semente fixa (42): rodar de novo produz os mesmos arquivos.

- Para cada equipamento há uma média de eventos por dia e uma faixa de duração. Cada loja tem um
  equipamento com desperdício bem acima dos outros (`expositor-2` na padaria, `iluminacao-estoque` no
  mercado), para verificar se a IA aponta o equipamento certo.
- Eventos de porta aberta acontecem dentro do horário de funcionamento da loja; eventos de luz acesa
  sem necessidade acontecem dentro e depois do horário.
- O custo de cada evento usa a fórmula do guia: `potencia_kw × fator_perda × (duracao_s / 3600) × tarifa_rs_kwh`,
  com os valores provisórios do guia para refrigeração (0,50 kW, 0,30 e R$ 0,90/kWh).
- Para iluminação o guia não define potência. A simulação adota 0,40 kW no salão e 0,12 kW no estoque,
  com fator de perda 1,0 (luz acesa sem ninguém é toda desperdício). É uma premissa do simulador, sem fonte.

Nenhum dado pessoal aparece nesses arquivos: só identificadores de loja e de equipamento fictícios.
