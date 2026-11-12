# Base de conhecimento

| Arquivo | O que é |
|---|---|
| `fontes.json` | uma entrada por documento: órgão, título, URL, formato, licença, data da fonte e data de acesso |
| `trechos.jsonl` | um trecho por linha: `id`, `doc_id`, `titulo`, `localizador` (onde está no documento) e `texto` |
| `indice/` | embeddings dos trechos (`bge-m3`), gerados por `python scripts/avaliar_busca.py` |

## Como os trechos foram feitos

1. Cada documento foi baixado da URL registrada em `fontes.json` em 10/11/2026 e convertido para texto.
2. O texto foi cortado por assunto, um trecho para cada ideia que responde a uma pergunta do comerciante
   (de 197 a 722 caracteres, mediana de 406), e não por tamanho fixo. Assim cada trecho se sustenta sozinho quando é citado.
3. Cada trecho recebeu um título descritivo, que entra junto com o texto no embedding, e um `localizador`
   (seção, item ou página) para quem quiser conferir no original.

## Transcrição ou síntese

O campo `tipo_trecho` de cada fonte diz como o texto foi escrito:

- **literal**: transcrição do original com cortes e junção de frases, sem mudar o sentido. Em poucas
  frases a redação foi ajustada para o trecho se sustentar sozinho (por exemplo, trocar "clique aqui"
  pela descrição de onde consultar); os números e as regras são os da fonte. Usada só onde a
  licença permite cópia: páginas do portal gov.br (CC BY-ND 3.0), ato oficial da Anvisa (sem proteção
  autoral, Lei 9.610/1998, art. 8º, IV) e o documento do próprio grupo.
- **sintese**: texto escrito pelo grupo a partir da fonte, começando com "Síntese:". Usada no livro do
  PROCEL/Eletrobras e na página da EPE, que não trazem licença de reprodução.

## Limites conhecidos da base

- Os valores das bandeiras tarifárias são os que constam na página da ANEEL consultada em 10/11/2026.
  A ANEEL revisa esses valores; antes de usar em produção, a base precisa ser atualizada.
- A base não traz tarifas por distribuidora, horários de ponta por distribuidora nem preços de
  equipamentos. Perguntas sobre isso devem ser recusadas ("não consta"), e o conjunto de teste confere isso.
- Os valores `produto-contrato-02` (tarifa, potência e fator de perda) são provisórios, como o próprio
  trecho avisa.
- Materiais do Sebrae sobre eficiência energética em minimercados e padarias seriam úteis, mas os
  arquivos não estavam mais disponíveis nos endereços encontrados e o conteúdo tem direitos reservados.

## Como acrescentar uma fonte

1. Adicione o documento em `fontes.json` com URL, formato e licença.
2. Adicione os trechos em `trechos.jsonl` com ids no padrão `<doc_id>-NN`.
3. Rode `python scripts/avaliar_busca.py` para refazer o índice e medir o recall.
4. Acrescente casos de teste em `avaliacao/casos_teste.jsonl` e rode `python scripts/avaliar.py`.
