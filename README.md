# Mobilidade e mercado imobiliário no Rio de Janeiro

Trabalho de AEDV — FGV EMAp, 2026.2. Transações residenciais do ITBI de 2011–2024 e Metrô, BRT, VLT e BRS.

## Organização

- `notebooks/01_itbi.ipynb`: preparação e geocodificação — Mayara.
- `notebooks/02_mobilidade.ipynb`: dados de transporte — Ana Alice.
- `notebooks/03_integracao_itbi.ipynb`: integração e distâncias — Ana Alice.
- `notebooks/04_analise_imobiliaria.ipynb`: contribuição de Henrique, a integrar.
- `notebooks/05_artigo.ipynb`: artigo da entrega parcial.
- `data/raw/`: planilhas e GeoJSON originais.
- `data/processed/`: base residencial completa geocodificada, base integrada com distâncias e camadas de transporte preparadas.

## Execução

Instale as bibliotecas com `python -m pip install -r requirements.txt` e abra os notebooks no VS Code/Jupyter, a partir da raiz ou de `notebooks/`.

Os CSVs grandes estão compactados em `.csv.gz`; o pandas lê esse formato diretamente. O artigo pode ser reexecutado com a base integrada incluída. Os notebooks 01 → 02 → 03 permitem refazer o processamento, mas **não é necessário repetir a geocodificação para analisar os dados já prontos**.

Henrique pode começar no notebook 04 lendo `data/processed/itbi_residencial_2011_2024_geocodificado_completo.csv.gz`. A base inclui a limpeza de Mayara, coordenadas, indicadores de qualidade e preços extremos sinalizados. A localização tem disponibilidade e precisão variáveis: confira `qualidade_geocodificacao`, `lat_analise` e `lon_analise`. Henrique fará as perguntas 1 a 4; a pergunta 8 fica com Mayara. Cada análise deve justificar seus próprios filtros e agregações.

As análises de transporte são parciais e serão completadas para as quatro modalidades. Valores são nominais; 2011 contém julho a dezembro. Lotes de geocodificação, caches e intermediários não acompanham o repositório.

## Fontes

[ITBI municipal](https://fazenda.prefeitura.rio/itbi-valores-medios-por-m2-de-transacoes-imobiliarias-por-trecho-de-logradouro/); [Metrô](https://www.data.rio/datasets/PCRJ::esta%C3%A7%C3%B5es-metr%C3%B4/about), [BRT](https://www.data.rio/datasets/f753941f44a749d4987f1111aa6486b3_0/about), [VLT](https://www.data.rio/datasets/29cc383d2d344e8387dda153ec0d545d_9/explore) e [BRS](https://www.data.rio/datasets/0b707ee14f3d4515ab513e7d078f0c1b_0/explore) — Data.Rio. Acesso aos datasets: 17 set. 2026.

A base original do VLT não informava inauguração; o grupo acrescentou anos de operação com as fontes históricas citadas no artigo (acesso: 21 out. 2026). Itamaraty permanece sem ano identificado. O teste caminhável usa OpenStreetMap/OSMnx.
