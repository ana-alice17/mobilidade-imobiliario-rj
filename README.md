# Mobilidade e mercado imobiliário no Rio de Janeiro

Trabalho de AEDV — FGV EMAp, 2026.2. Transações residenciais do ITBI de 2011–2024 e Metrô, BRT, VLT e BRS.
## Apoio Visual para o Segundo Marco:
- `https://canva.link/q7hssai3iz5cr3n`
## Organização

- `notebooks/01_itbi.ipynb`: preparação e geocodificação — Mayara.
- `notebooks/02_mobilidade.ipynb`: dados de transporte — Ana Alice.
- `notebooks/03_integracao_itbi.ipynb`: integração e distâncias — Ana Alice.
- `notebooks/04_analise_imobiliaria.ipynb`: análise descritiva do preço do m² (perguntas 1 a 4) — Henrique.
- `notebooks/05_artigo.ipynb`: artigo da entrega parcial.
- `data/raw/`: planilhas e GeoJSON originais.
- `data/processed/`: base residencial completa geocodificada, base integrada com distâncias e camadas de transporte preparadas.

## Execução

Instale as bibliotecas com `python -m pip install -r requirements.txt` e abra os notebooks no VS Code/Jupyter, a partir da raiz ou de `notebooks/`.

Os CSVs grandes estão compactados em `.csv.gz`; o pandas lê esse formato diretamente. O artigo pode ser reexecutado com as bases incluídas em `data/processed/`. Os notebooks 01 → 02 → 03 permitem refazer o processamento, mas **não é necessário repetir a geocodificação para analisar os dados já prontos**.

O notebook 04 lê `data/processed/itbi_residencial_2011_2024_geocodificado_completo.csv.gz`, exclui as transações com `valor_m2_suspeito` (preços extremos sinalizados no notebook 01), corrige os valores pelo IPCA para reais de dezembro de 2024 e associa cada bairro à sua Área de Planejamento. Os mapas usam só as coordenadas de alta precisão (`lat_analise` e `lon_analise`). Os resultados das perguntas 1 a 4 estão nas seções 5.1 a 5.4 do artigo, que repete esses cálculos; a pergunta 8 fica com Mayara. Cada análise deve justificar seus próprios filtros e agregações.

As análises de transporte são parciais e serão completadas para as quatro modalidades. Valores são nominais, exceto no notebook 04 e nas seções 5.1 a 5.4 do artigo, corrigidos pelo IPCA; 2011 contém julho a dezembro. Lotes de geocodificação, caches e intermediários não acompanham o repositório.

## Fontes

[ITBI municipal](https://fazenda.prefeitura.rio/itbi-valores-medios-por-m2-de-transacoes-imobiliarias-por-trecho-de-logradouro/); [Metrô](https://www.data.rio/datasets/PCRJ::esta%C3%A7%C3%B5es-metr%C3%B4/about), [BRT](https://www.data.rio/datasets/f753941f44a749d4987f1111aa6486b3_0/about), [VLT](https://www.data.rio/datasets/29cc383d2d344e8387dda153ec0d545d_9/explore) e [BRS](https://www.data.rio/datasets/0b707ee14f3d4515ab513e7d078f0c1b_0/explore) — Data.Rio. Acesso aos datasets: 17 set. 2026. Correção monetária pelo IPCA (IBGE) e Áreas de Planejamento segundo a divisão administrativa do Instituto Pereira Passos.

A base original do VLT não informava inauguração; o grupo acrescentou anos de operação com as fontes históricas citadas no artigo (acesso: 21 out. 2026). Itamaraty permanece sem ano identificado. O teste caminhável usa OpenStreetMap/OSMnx.
