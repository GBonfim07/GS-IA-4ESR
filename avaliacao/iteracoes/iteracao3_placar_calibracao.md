# Placar (calibracao)

Modelo: `qwen2.5:7b` · embeddings: `bge-m3` · limiar de recusa: 0.56 · 30 casos

| Configuração | Acerto | Alucinação | Acerto (respondíveis) | Recusa correta (não consta) | Recusa indevida | Citação correta | JSON válido | Tempo médio (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1. Modelo puro | 43.3% | 10.0% | 28.6% | 77.8% | 33.3% | 0.0% | 100.0% | 2.70 |
| 2. RAG simples | 86.7% | 0.0% | 81.0% | 100.0% | 14.3% | 94.4% | 100.0% | 2.70 |
| 3. Agente com ferramentas | 100.0% | 0.0% | 100.0% | 100.0% | 0.0% | 95.2% | 100.0% | 8.44 |

## Acerto por categoria

| Configuração | Factual | Cálculo | Loja | Não consta |
|---|---:|---:|---:|---:|
| 1. Modelo puro | 37.5% | 0.0% | 0.0% | 77.8% |
| 2. RAG simples | 100.0% | 33.3% | 0.0% | 100.0% |
| 3. Agente com ferramentas | 100.0% | 100.0% | 100.0% | 100.0% |
