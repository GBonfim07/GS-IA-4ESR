# Segunda execução do conjunto de teste

O placar oficial do relatório é o de `avaliacao/resultados/` (primeira execução, com revisão manual de
todas as respostas). Esta pasta guarda uma **segunda execução completa**, feita em 11/11/2026 na mesma
máquina, com o mesmo código, o mesmo modelo, temperatura 0 e a mesma semente, para medir quanto o
resultado varia de uma rodada para outra.

## O que mudou entre as duas execuções

| Configuração | Respostas com texto idêntico | Decisão idêntica (responder ou recusar) | Casos em que a correção mudou |
|---|---:|---:|---|
| 1. Modelo puro | 33 de 44 | 43 de 44 | `t39`: na primeira inventou um prazo de 12 meses; na segunda recusou |
| 2. RAG simples | 41 de 44 | 44 de 44 | nenhum |
| 3. Agente com ferramentas | 34 de 44 | 44 de 44 | `t10`: na primeira respondeu "5 ºC" (certo); na segunda, "4 ºC" (errado) |

| Configuração | Acerto, 1ª execução | Acerto, 2ª execução | Alucinação, 1ª | Alucinação, 2ª |
|---|---:|---:|---:|---:|
| 1. Modelo puro | 31,8% | 34,1% | 40,9% | 38,6% |
| 2. RAG simples | 72,7% | 72,7% | 2,3% | 2,3% |
| 3. Agente com ferramentas | 90,9% | 88,6% | 4,5% | 6,8% |

A ordem das três configurações e o tamanho das diferenças não mudam. Cada configuração variou em no
máximo um caso (2,3 pontos percentuais). Os quatro erros do agente analisados no relatório (`t19`,
`t21`, `t26` e `t32`) se repetiram na segunda execução.

## Por que varia

O que foi medido: temperatura 0 e semente fixa não bastaram para a geração sair idêntica de uma rodada
para outra no Ollama. A causa não foi investigada. A hipótese mais provável é a aritmética em ponto
flutuante na GPU, cujo resultado pode depender do estado deixado pela chamada anterior; quando duas
palavras têm probabilidade quase igual, a escolha vira. Na maior parte dos casos muda só a redação.

## Como ler os arquivos

- `teste_<config>.jsonl`: resposta completa e correção de cada caso, no mesmo formato de `avaliacao/resultados/`.
- `placar_teste_repeticao.md`: placar gerado pelo script para esta execução.

A revisão manual (`avaliacao/revisao_manual.json`) foi escrita para a primeira execução. Nas respostas
que mudaram de texto, as notas foram conferidas de novo e continuam valendo, com um acréscimo: no caso
`t10` do agente, a resposta "4 ºC" contradiz o gabarito ("inferior a 5 ºC") e conta como alucinação. Por
isso a alucinação do agente nesta execução é de 3 casos em 44 (6,8%), e não os 4,5% que o placar
automático desta pasta mostra.
