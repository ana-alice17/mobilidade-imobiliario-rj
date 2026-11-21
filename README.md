# Mobilidade urbana e mercado imobiliário no Rio de Janeiro

Projeto final de Análise Exploratória de Dados e Visualização, FGV EMAp, 2026.2.

## Ler o trabalho

O artigo é o notebook `notebooks/05_artigo.ipynb`: capa no padrão FGV EMAp/ABNT, as oito perguntas da proposta com respostas diretas, gráficos, um explorador interativo e a conclusão. Os enunciados originais estão em `PROPOSTA_ORIGINAL.md`. Os notebooks 01 a 04 são os bastidores: 01 trata o ITBI, 02 organiza os dados de transporte, 03 cruza imóveis e acessos e 04 explora o mercado.

O explorador interativo (seção 5.9) responde "o que muda quando alteramos a distância ou trocamos a mediana pela média?", com controles de corte (500/800/1.000/1.500 m) e de medida de centro (média/mediana), via ipywidgets.

## Recortes

- **Perguntas 1–4 e 8:** mercado residencial de julho de 2011 a dezembro de 2024 (440.155 transações, sem os extremos sinalizados). Em 2011 há seis meses na base; a série temporal compara também a janela julho–dezembro de cada ano. Valores corrigidos pelo IPCA mensal oficial para reais de dezembro de 2024.
- **Perguntas 5–7:** Metrô, BRT e VLT em todo o período (318.709 transações com geocodificação de alta precisão, 2011–2024); BRS apenas em 2024 (32.320 das 43.670 vendas do ano), único ano com cadastro de pontos verificável. Cada modalidade entra a partir de quando seus acessos existem: BRT desde 2013, VLT desde 2017 (ano seguinte ao da inauguração cadastrada).
- **Proximidade:** menor percurso a pé até o acesso, corte principal de 1 km, com checagens a 500, 800 e 1.500 m. Só entram no denominador os registros com percurso calculado e sem acesso omitido capaz de mudar a classificação.

## Executar

Com Python 3.12 ou mais recente, na raiz do projeto:

```text
python -m pip install -r requirements.txt
```

Abra e execute os notebooks na ordem 01 → 02 → 03 → 04 → 05. A execução padrão reaproveita as coordenadas e os percursos já calculados em `data/processed/` e os geocódigos publicados em `cache/geocodificacao/`; não faz novas consultas externas. A leitura das bases grandes pode levar alguns minutos.

## Dados e saídas

- `data/raw/`: fontes originais (planilhas ITBI, camadas de transporte, GTFS BRS de 2024, série IPCA).
- `data/processed/`: bases residenciais com distâncias e percursos a pé já calculados.
- `resultados/historico/`: tabelas do recorte 2011–2024 de Metrô, BRT e VLT (resumo perto/longe, dispersão, três níveis de comparação, composição por AP, sensibilidade).
- `resultados/proposta/`: tabelas do BRS em 2024 e dos bastidores.
- `resultados/pergunta_8_anual.csv` e demais CSVs da raiz: série anual e resumos do mercado.

## Documentação

`METODOLOGIA.md` resume as escolhas de método; `CAMINHADA.md` descreve o cálculo dos percursos a pé; `FONTES_BRS.md` e `FONTES_EVENTOS.md` documentam as fontes. O mapa cadastral usa o limite municipal, a costa e as vias principais do OpenStreetMap (© contribuidores do OpenStreetMap, ODbL) com as camadas de transporte do Data.Rio.

O ITBI registra compras e vendas. As análises são descritivas: as diferenças observadas entre grupos não demonstram efeito causal do transporte sobre o preço de venda.
