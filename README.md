# Mobilidade e mercado imobiliário no Rio de Janeiro

Trabalho de AEDV - FGV EMAp, 2026.2. Transações residenciais do ITBI de 2011–2024 e Metrô, BRT, VLT e BRS.
## Apoio Visual para o Segundo Marco:
- `https://canva.link/q7hssai3iz5cr3n`
## Organização

- `notebooks/01_itbi.ipynb`: preparação e geocodificação.
- `notebooks/02_mobilidade.ipynb`: dados de transporte
- `notebooks/03_integracao_itbi.ipynb`: integração e distâncias
- `notebooks/04_analise_imobiliaria.ipynb`: análise descritiva do preço do m² (perguntas 1 a 4)
- `notebooks/05_artigo.ipynb`: artigo.
- `data/raw/`: planilhas e GeoJSON originais.
- `data/processed/`: base residencial completa geocodificada, base integrada com distâncias e camadas de transporte preparadas.

## Execução

Instale as bibliotecas com `python -m pip install -r requirements.txt` e abra os notebooks no VS Code/Jupyter, a partir da raiz ou de `notebooks/`.

Os CSVs grandes estão compactados em `.csv.gz`; o pandas lê esse formato diretamente. O artigo pode ser reexecutado com as bases incluídas em `data/processed/`. Os notebooks 01 → 02 → 03 permitem refazer o processamento, mas **não é necessário repetir a geocodificação para analisar os dados já prontos**.

A base original do VLT não informava inauguração; o grupo acrescentou anos de operação com as fontes históricas citadas no artigo (acesso: 21 out. 2026). Itamaraty permanece sem ano identificado. O teste caminhável usa OpenStreetMap/OSMnx.
