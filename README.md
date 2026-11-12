# Energia que dá Lucro · Consultor de Eficiência Energética

**FIAP · Global Solution 2026.2 · CitizenTech · 4ES · Generative AI for Engineering**
Componente **Inteligência** do produto: uma LLM local que recomenda ao comerciante como reduzir o desperdício de energia, citando a fonte, e que responde "não consta" quando a base não cobre o assunto.

| Configuração (mesmo modelo, 44 casos de teste) | Acerto | Alucinação |
|---|---:|---:|
| 1. Modelo puro, sem contexto | 31,8% | 40,9% |
| 2. RAG simples | 72,7% | 2,3% |
| 3. Agente com ferramentas | **90,9%** | 4,5% |

O relatório completo, com diagrama, tabela da base, placar interpretado e os cinco erros, está em **[RELATORIO.md](RELATORIO.md)**.

## Integrantes

| Nome completo | RM |
|---|---|
| Gustavo Henrique Santos Bonfim | RM98864 |
| João Pedro Marques | RM98307 |
| Kayky Paschoal Ribeiro | RM99929 |
| Lucas Yuji Farias Umada | RM99757 |
| Natan Eguchi dos Santos | RM98720 |

## Ficha Técnica do MVP

| Campo | Conteúdo |
|---|---|
| Nome do produto | Energia que dá Lucro (nome provisório) |
| Cidadão e território | Donos e funcionários de pequenos comércios de bairro (mercadinhos, padarias, açougues, lojas) em cidades brasileiras |
| Problema, em uma frase | O pequeno comerciante paga caro de energia sem saber quais hábitos e equipamentos causam o desperdício |
| Proposta de valor | Mostrar o desperdício em reais, avisar na hora em que ele acontece e sugerir ações simples, usando as câmeras que a loja já tem |
| Arquitetura: componentes | Detecção por câmera (Visão) · robô com sensores (Físico) · API e painel do comerciante (Produção) · pipeline de dados (Dados) · **consultor de eficiência com LLM local (Inteligência, este repositório)** · alertas e resumos automáticos (Automação) · modelo de negócio (Pitch) |
| Fontes de dados | Clima (Open-Meteo) · tarifas e bandeiras (ANEEL) · eventos e consumo das lojas (simulados, com geração documentada) |
| Modelos de IA utilizados | YOLO treinado para portas de refrigeração abertas · **LLM local `qwen2.5:7b` com base de conhecimento (RAG) e agente com ferramentas; embeddings `bge-m3`** · IA embarcada no robô |
| URL do MVP e repositório | MVP: sem URL pública nesta entrega. É uma landing page com um painel administrativo em que o cliente vê os dashboards; o painel recebe o JSON de recomendações gerado aqui (`saida/recomendacoes.json`) · Repositório: <https://github.com/GBonfim07/GS-IA-4ESR> |
| Indicadores de impacto | R$ e kWh de desperdício evitados por loja ao mês · tempo médio de porta aberta · percentual de alertas resolvidos em poucos minutos · número de lojas ativas |
| ODS conectados | ODS 7 e ODS 12 (mais diretos); do slide oficial, ODS 9, 11 e 13 |

**O que a IA resolve.** O painel mostra quanto a loja desperdiçou; o Consultor diz o que fazer. Ele recebe o resumo de desperdício da loja ou uma pergunta do comerciante e devolve uma recomendação em JSON com a fonte citada. **ODS 7:** reduz o consumo de energia do pequeno comércio com orientação de fontes oficiais. **ODS 12:** ataca o desperdício sem comprometer a conservação dos alimentos, porque a base inclui as temperaturas exigidas pela Anvisa.

## O que há no repositório

```
base/           fontes.json (14 fontes com URL e licença), trechos.jsonl (56 trechos), indice/
avaliacao/      casos_teste.jsonl (74 casos com gabarito), resultados/, placar_teste.md,
                revisao_manual.json, erros_selecionados.json, limiar.json, iteracoes/,
                repeticao/ (segunda execução do teste, para medir a variação entre rodadas)
notebooks/      01 base e busca · 02 geração com RAG · 03 agente · 04 placar e erros (saídas salvas)
src/consultor/  busca, geração, agente, ferramentas, avaliação e API
scripts/        avaliar_busca.py · avaliar.py · gerar_recomendacoes.py · simular_eventos.py · montar_notebooks.py
dados/          eventos e resumos simulados das lojas (entrada)
saida/          recomendacoes.json (o que o painel e a automação consomem)
tests/          testes que rodam sem a LLM
docs/           contrato de dados com o painel
```

| Critério da rubrica | Onde está |
|---|---|
| 01 Tarefa da IA e casos de teste com gabarito, incluindo "não consta" | [RELATORIO.md §02](RELATORIO.md) · [`avaliacao/casos_teste.jsonl`](avaliacao/casos_teste.jsonl) (21 casos "não consta") |
| 02 Base de conhecimento, em trechos com fonte | [`base/`](base/) · [RELATORIO.md §04](RELATORIO.md) · notebook 01 |
| 03 Busca com recall@1 e recall@3 medidos e limiar justificado | notebook 01 · [RELATORIO.md §5.2 e §5.3](RELATORIO.md) · [`avaliacao/busca.json`](avaliacao/busca.json) |
| 04 Geração fundamentada: JSON válido, citação da fonte e recusa | [`src/consultor/geracao.py`](src/consultor/geracao.py) · notebook 02 |
| 05 Especialização (agente) comparada ao RAG simples | [`src/consultor/agente.py`](src/consultor/agente.py) · notebook 03 |
| 06 Placar das três configurações, com resultados interpretados | [RELATORIO.md §5.4 e §5.5](RELATORIO.md) · notebook 04 · [`avaliacao/placar_teste.md`](avaliacao/placar_teste.md) |
| 07 Cinco erros reais com proposta de correção | [RELATORIO.md §06](RELATORIO.md) · notebook 04 · [`avaliacao/erros_selecionados.json`](avaliacao/erros_selecionados.json) |
| 08 README e reprodutibilidade | este arquivo |

## Como reproduzir

Testado em Windows 11, Python 3.13, Ollama 0.40.16 e GPU Radeon RX 7800 XT (16 GB). Funciona também só com CPU, mais devagar. São necessários cerca de 6 GB de disco para os modelos.

**1. Instale o Ollama** ([ollama.com](https://ollama.com)) e baixe os dois modelos:

```bash
ollama pull qwen2.5:7b
```

```bash
ollama pull bge-m3
```

**2. Instale as dependências do Python** (3.11 ou mais novo):

```bash
pip install -r requirements.txt
```

**3. Rode os testes que não dependem da LLM** (base, ferramentas, contrato e API):

```bash
python -m pytest -q
```

**4. Monte o índice, meça a busca e calibre o limiar** (cerca de 1 minuto):

```bash
python scripts/avaliar_busca.py
```

**5. Rode o placar das três configurações** (cerca de 10 minutos com GPU):

```bash
python scripts/avaliar.py
```

O placar sai em `avaliacao/placar_teste.md` e cada resposta fica em `avaliacao/resultados/`. Este comando sobrescreve as respostas gravadas.

**O que esperar ao repetir.** A geração usa temperatura 0 e semente fixa, mas isso não torna o resultado idêntico bit a bit no Ollama. Repetimos a medição inteira na mesma máquina ([`avaliacao/repeticao/`](avaliacao/repeticao/)): o RAG deu o mesmo placar, e o modelo puro e o agente mudaram em um caso cada (agente: 90,9% na primeira execução e 88,6% na segunda). Espere números próximos dos publicados, com diferença de um ou dois casos. Como `avaliacao/revisao_manual.json` foi escrito para as respostas gravadas aqui, ele precisa ser conferido de novo se as respostas mudarem; a coluna "Alucinação (só automática)" não depende dele.

**6. Gere o arquivo de recomendações que o painel consome:**

```bash
python scripts/gerar_recomendacoes.py
```

**7. Suba a API local:**

```bash
python -m uvicorn consultor.api:app --app-dir src --host 127.0.0.1 --port 8000
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`.

**8. (Opcional) Reexecute os notebooks**, gravando as saídas:

```bash
python scripts/montar_notebooks.py
```

No Windows, se os acentos saírem trocados no terminal, rode os scripts com `python -X utf8`.

## API

| Rota | O que faz |
|---|---|
| `POST /recomendar` | recebe `{"pergunta", "configuracao": "agente" \| "rag" \| "puro", "loja_id", "periodo"}` e devolve a recomendação no contrato do produto, mais o campo `explicacao` |
| `POST /recomendar/resumo` | recebe `{"loja_id", "periodo", "resumo"}` (formato do `GET /summary` do painel) e devolve uma recomendação para cada equipamento que mais desperdiçou |
| `GET /trechos/{trecho_id}` | mostra o trecho citado, com documento, órgão, URL e licença |
| `GET /health` | estado do Ollama, modelos e limiar em uso |

Exemplo de resposta real de `POST /recomendar` para a pergunta "Quanto custa deixar o freezer aberto por 8 horas no total, com os valores do produto?":

```json
{
  "loja_id": "padaria-01",
  "periodo": "2026-11",
  "nao_consta": false,
  "recomendacao": "O custo estimado para deixar o freezer aberto por 8 horas é de R$ 1.08.",
  "fonte": {
    "titulo": "Energia que dá Lucro — Guia do grupo, seção 3 (formato de dados comum e fórmula do custo estimado)",
    "trecho_id": "produto-contrato-01"
  },
  "explicacao": {
    "configuracao": "agente",
    "decisao": "resposta",
    "ferramentas_usadas": [
      {"ferramenta": "buscar_base", "argumentos": {"consulta": "..."}},
      {"ferramenta": "calcular_custo_desperdicio", "argumentos": {"duracao_valor": 8, "unidade": "h"}}
    ],
    "segundos": 9.18
  }
}
```

Quando a base não tem a resposta, a saída é `{"nao_consta": true, "recomendacao": "", "fonte": null}`.

## Ligação com o resto do produto

| | |
|---|---|
| Entrada | resumo da loja no formato do `GET /summary`. Hoje vem de `dados/` (simulado, ver [`dados/README.md`](dados/README.md)); com a variável `PAINEL_URL` definida, vem da API do painel |
| Saída | [`saida/recomendacoes.json`](saida/recomendacoes.json): lista de recomendações para `padaria-01` e `mercado-01`, no contrato da seção 3 do guia. O painel exibe na tela de sugestões e a automação (RPA) usa o texto no e-mail |
| Contrato | [`docs/contrato_de_dados.md`](docs/contrato_de_dados.md) |

## Segurança, LGPD e IA responsável

- **Tudo local.** A LLM e os embeddings rodam no Ollama da própria máquina. Nenhuma pergunta ou dado de loja é enviado a serviços externos.
- **Sem dados pessoais.** O componente recebe identificadores de loja e de equipamento, nunca imagens, nomes ou contatos. A API não grava a pergunta; o log guarda só um hash dela.
- **Sem segredos no repositório.** A chave opcional da API vem da variável `CONSULTOR_API_KEY` ([`.env.example`](.env.example)).
- **Explicável.** Toda resposta cita o trecho que a sustenta e traz o campo `explicacao` (decisão, trechos consultados, similaridade, limiar e ferramentas usadas).
- **Pessoa na decisão.** O sistema só sugere. Quem decide e age é o comerciante.
- **Defesas.** Limite de tamanho da pergunta, instrução para tratar a pergunta e os trechos como dados (teste de injeção no notebook 02), calculadora que só aceita aritmética e API escutando apenas em `127.0.0.1`. O resumo recebido em `/recomendar/resumo` é validado campo a campo antes de chegar à LLM, e o valor em reais de cada recomendação em lote é conferido contra o resumo: se divergir, a recomendação é descartada.

## Limites conhecidos

- O conjunto de teste tem 44 casos; cada caso vale 2,3 pontos percentuais.
- O placar varia em até um caso por configuração de uma rodada para outra (medido em `avaliacao/repeticao/`).
- O gabarito e a revisão manual foram feitos pelo grupo. As respostas completas estão em `avaliacao/resultados/` para conferência.
- Os valores da fórmula de custo (R$ 0,90/kWh, 0,50 kW e 0,30) são provisórios, como o guia do grupo avisa.
- Os valores das bandeiras tarifárias são os da página da ANEEL consultada em 10/11/2026.
- As correções propostas para os cinco erros ainda não foram implementadas.

