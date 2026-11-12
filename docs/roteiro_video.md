# Roteiro sugerido para o vídeo

O vídeo é opcional: os entregáveis e a pontuação da disciplina não o pedem. Ele só aparece no slide de
entregas, no item 07 do relatório ("links do repositório e do vídeo"), sem duração nem conteúdo. Esta é uma sugestão de
cerca de 4 minutos; confirmem com o professor antes de gravar.

| Tempo | O que mostrar | O que dizer |
|---|---|---|
| 0:00 | Slide com o nome do produto e dos integrantes | O problema: o comerciante vê quanto desperdiçou, mas não sabe o que fazer. A IA responde com fonte ou diz "não consta". |
| 0:30 | `base/fontes.json` e duas linhas de `base/trechos.jsonl` | 14 fontes públicas (ANEEL, Anvisa, PROCEL), 56 trechos, cada um com fonte e licença. |
| 1:00 | Notebook 02, seções 1 e 2 | A mesma pergunta no modelo puro e no RAG: o RAG cita o trecho; a pergunta fora da base é recusada. |
| 1:45 | Notebook 03, seções 1 e 3 | O agente chama a calculadora e lê o resumo da loja. Mostrar as ferramentas escolhidas. |
| 2:30 | Notebook 04, tabela e gráfico do placar | Acerto 31,8%, 72,7% e 90,9%. Alucinação 40,9%, 2,3% e 4,5%. O que cada número significa. |
| 3:15 | Notebook 04, dois dos cinco erros | Um erro do limiar e o erro de aritmética, com a correção proposta. |
| 3:45 | `saida/recomendacoes.json` e a API em `/docs` | Como o painel e a automação consomem a saída. Tudo roda local. |

Dicas: grave a tela com o Ollama já aberto, para as respostas saírem rápido, e teste o link em janela anônima.
