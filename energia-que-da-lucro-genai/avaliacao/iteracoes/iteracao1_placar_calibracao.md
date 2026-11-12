# Placar (calibracao)

Modelo: `qwen2.5:7b` · embeddings: `bge-m3` · limiar de recusa: 0.56 · 30 casos

| Configuração | Acerto | Alucinação | Acerto (respondíveis) | Recusa correta (não consta) | Recusa indevida | Citação correta | JSON válido | Tempo médio (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1. Modelo puro | 46.7% | 6.7% | 23.8% | 100.0% | 57.1% | 0.0% | 100.0% | 2.71 |
| 2. RAG simples | 66.7% | 0.0% | 52.4% | 100.0% | 33.3% | 100.0% | 100.0% | 2.15 |
| 3. Agente com ferramentas | 43.3% | 6.7% | 19.0% | 100.0% | 66.7% | 100.0% | 100.0% | 4.28 |

## Acerto por categoria

| Configuração | Factual | Cálculo | Loja | Não consta |
|---|---:|---:|---:|---:|
| 1. Modelo puro | 31.2% | 0.0% | 0.0% | 100.0% |
| 2. RAG simples | 68.8% | 0.0% | 0.0% | 100.0% |
| 3. Agente com ferramentas | 18.8% | 33.3% | 0.0% | 100.0% |
