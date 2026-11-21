# Distâncias pela rede de caminhada

Este documento descreve como os percursos a pé foram calculados. As distâncias já
calculadas acompanham a entrega em `data/processed/itbi_com_caminhada.csv.gz`
(Metrô, BRT e VLT, 2011–2024) e `data/processed/acesso_2024_caminhada.csv.gz`
(as quatro modalidades, incluindo o BRS, em 2024). Os comprimentos em metros provêm
da geometria da rede em SIRGAS 2000 / UTM 23S (EPSG:31983). Não há multiplicador de
distância em linha reta.

## O que o cálculo representa

Cada origem e acesso é projetado no segmento de rua permitido a pedestres mais
próximo. O percurso é a soma do conector curto da origem, do menor caminho na rede
e do conector do acesso. Os conectores, medidos em linha reta, são uma aproximação
local explícita: não se modela a porta do imóvel. Rejeitam-se origens com conector
superior a 100 m e acessos com conector superior a 60 m. Não se preenchem distâncias
ausentes com valores euclidianos.

Os IDs dos nós OSM preservam a topologia: cruzamentos de ruas com viadutos sem nó
compartilhado não viram interseções. Excluem-se vias de acesso privado ou proibido
a pedestres e vias motorizadas de acesso controlado sem permissão explícita para
pedestres. Respeita-se `oneway:foot`, e não a mão única dos automóveis. Escadas são
permitidas; o resultado não é um indicador de acessibilidade em cadeira de rodas.

O algoritmo usa Dijkstra em grafo esparso com uma superorigem, incorporando o custo
de todos os acessos de cada modalidade. Seleciona o acesso com menor percurso,
que pode ser diferente da estação mais próxima em linha reta. A projeção na mesma
aresta é tratada diretamente para evitar obrigar o pedestre a passar por um nó
desnecessário. Arestas paralelas usam o menor custo, sem somar duplicações.

## Acessos e disponibilidade

- **Metrô:** entradas OSM `railway=subway_entrance` a até 350 m do ponto oficial,
  atribuídas à estação oficial mais próxima. Estações sem entrada conectada não são
  substituídas pelo centro da estação.
- **BRT e VLT:** ponto oficial da parada de superfície, conectado à rede em até
  60 m. Esses pontos são aproximações do acesso e não constituem uma validação de
  todas as travessias, plataformas ou entradas históricas.
- **BRS:** em 2024, os 255 pontos de embarque nomeados no GTFS oficial (FONTES_BRS.md).
  Não se apresenta caminhada até uma linha de corredor como se fosse até um ponto
  de ônibus; por isso o BRS não entra no recorte histórico de 2011–2023.

No cenário histórico, entram somente estações com ano de início anterior ao ano da
transação, pelo critério conservador de considerar o ano seguinte ao da inauguração
cadastrada (BRT desde 2013, VLT desde 2017). Quando só se conhece o ano, não se
presume abertura em janeiro. A distância às inaugurações do próprio ano e às
estações sem data é calculada separadamente para identificar classificações
indeterminadas.

Um percurso até uma entrada mapeada comprova somente uma rota no modelo. Se uma
estação excluída por acesso ausente puder estar dentro do limiar, uma classificação
"longe" fica indeterminada. A distância euclidiana a esses objetos é usada apenas
como limite inferior de incerteza, nunca como distância caminhável.

## Limites temporais e de interpretação

A rede é um extrato contemporâneo de outubro de 2026, aplicado aos anos de
2011–2024 com disponibilidade histórica das estações. **Não é uma reconstrução
histórica das ruas ou entradas.** Não modela obras temporárias, funcionamento
mensal, fechamento de estações, acessos inaugurados depois da estação, declividade,
semáforos, segurança ou existência/qualidade de calçadas. Conectores podem cruzar
obstáculos que ainda exijam verificação em campo. O tamanho do limiar não elimina
essas limitações.

Os resultados são associações descritivas na amostra geocodificada. Não equivalem
ao efeito causal de acesso ao transporte sobre o preço.

Dados OpenStreetMap © contribuidores do OpenStreetMap, disponibilizados sob
[ODbL](https://www.openstreetmap.org/copyright).
