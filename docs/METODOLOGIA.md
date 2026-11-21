# Notas de metodologia

Este documento resume as escolhas de método do artigo (`notebooks/05_artigo.ipynb`). Os detalhes de implementação estão nos notebooks 01–04 e nos módulos de `src/`.

## Recortes

As perguntas 1–4 e 8 usam a base residencial de julho de 2011 a dezembro de 2024: 440.155 transações, sem os extremos sinalizados pelo critério de 3×IIQ do log10 do preço por m² em cada ano. Como 2011 só tem o segundo semestre, a pergunta 8 também compara a janela julho–dezembro de cada ano.

As perguntas 5–7 usam as vendas com geocodificação de alta precisão. Para Metrô, BRT e VLT, todo o período (318.709 transações, 2011–2024). O BRS entra apenas com 2024 (32.320 transações), porque só desse ano há cadastro de pontos verificável: 255 pontos de embarque nomeados no GTFS oficial SMTR de abril de 2024 (versão 01Q0424), preservado pela TUMI/TDC. Não retroagimos esse cadastro aos anos anteriores. Cada modalidade é avaliada a partir de quando seus acessos existem: o BRT desde 2013 e o VLT desde 2017, pelo critério conservador de considerar o ano seguinte ao da inauguração cadastrada.

## Proximidade

A distância de referência é o menor percurso estimado na rede de pedestres do OpenStreetMap, com conectores curtos entre endereço, rede e acesso. O corte principal é 1 km; a sensibilidade é verificada a 500, 800 e 1.500 m. Só entram no denominador de cada modalidade os registros com percurso calculado e sem acesso omitido capaz de mudar a classificação. O extrato de ruas e entradas é de outubro de 2026, uma aproximação explicitada para os percursos de 2011–2024.

## Comparações

Além da comparação geral da cidade, comparamos perto e longe em três níveis: geral; restrito aos grupos de bairro e tipo com pelo menos dez transações e três locais distintos de cada lado; e mediana das diferenças calculadas dentro de cada grupo comparável, com o mesmo peso por grupo. A composição do grupo perto por Área de Planejamento, confrontada com o preço mediano de cada AP, mostra em que medida o contraste bruto reflete a localização dos acessos.

## Valores e contexto

Todos os valores monetários são corrigidos pelo IPCA mensal oficial (IBGE, tabela 1737, variável 2266) para reais de dezembro de 2024. Os anos de 2014 e 2016 são descritos no contexto das entregas de transporte e da recessão nacional, sem atribuição de causalidade à Copa ou aos Jogos.

As análises são descritivas: as diferenças observadas entre grupos não demonstram efeito causal do transporte sobre o preço de venda.
