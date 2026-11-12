# Placar (teste)

Modelo: `qwen2.5:7b` · embeddings: `bge-m3` · limiar de recusa: 0.56 · 44 casos

| Configuração | Acerto | Alucinação (com revisão manual) | Alucinação (só automática) | Recusa correta (não consta) | Recusa indevida | Citação correta | JSON válido | Tempo médio (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1. Modelo puro | 31.8% | 40.9% | 9.1% | 75.0% | 25.0% | 0.0% | 100.0% | 2.74 |
| 2. RAG simples | 72.7% | 2.3% | 0.0% | 100.0% | 34.4% | 100.0% | 100.0% | 2.21 |
| 3. Agente com ferramentas | 90.9% | 4.5% | 0.0% | 100.0% | 6.2% | 100.0% | 100.0% | 8.41 |

## Acerto por categoria

| Configuração | Factual | Cálculo | Loja | Não consta |
|---|---:|---:|---:|---:|
| 1. Modelo puro | 25.0% | 0.0% | 0.0% | 75.0% |
| 2. RAG simples | 90.0% | 33.3% | 0.0% | 100.0% |
| 3. Agente com ferramentas | 95.0% | 66.7% | 83.3% | 100.0% |
