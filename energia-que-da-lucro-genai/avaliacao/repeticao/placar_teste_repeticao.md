# Placar (teste)

Modelo: `qwen2.5:7b` · embeddings: `bge-m3` · limiar de recusa: 0.56 · 44 casos

| Configuração | Acerto | Alucinação (com revisão manual) | Alucinação (só automática) | Recusa correta (não consta) | Recusa indevida | Citação correta | JSON válido | Tempo médio (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1. Modelo puro | 34.1% | 38.6% | 6.8% | 83.3% | 25.0% | 0.0% | 100.0% | 3.12 |
| 2. RAG simples | 72.7% | 2.3% | 0.0% | 100.0% | 34.4% | 100.0% | 100.0% | 2.23 |
| 3. Agente com ferramentas | 88.6% | 4.5% | 0.0% | 100.0% | 6.2% | 100.0% | 100.0% | 8.80 |

## Acerto por categoria

| Configuração | Factual | Cálculo | Loja | Não consta |
|---|---:|---:|---:|---:|
| 1. Modelo puro | 25.0% | 0.0% | 0.0% | 83.3% |
| 2. RAG simples | 90.0% | 33.3% | 0.0% | 100.0% |
| 3. Agente com ferramentas | 90.0% | 66.7% | 83.3% | 100.0% |
