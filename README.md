# Mobilidade urbana e mercado imobiliário no Rio de Janeiro

Trabalho de Análise Exploratória de Dados e Visualização, FGV EMAp, 2026.2.
Ana Alice Silva, Henrique Lara e Mayara A. P. Bomback.

## Ler e apresentar

- [Artigo com resultados e gráficos](notebooks/05_artigo.ipynb).
- [Slides do marco 2](slides/marco_2.pdf) e [slides do marco 3](slides/marco_3.pdf).
- [Declaração de contribuições](docs/Declaração%20de%20contribuições.pdf).

O estudo descreve preços residenciais do ITBI de julho de 2011 a dezembro de
2024, corrigidos pelo IPCA para reais de dezembro de 2024. A base principal tem
440.155 vendas. As comparações de transporte usam geocodificação de alta precisão:
Metrô, BRT e VLT em 2011–2024, conforme a disponibilidade dos acessos, e BRS apenas
em 2024. Proximidade significa percurso a pé de até 1 km, com testes a 500, 800 e
1.500 m. As diferenças são descritivas e não identificam efeitos causais.

## Organização

- `notebooks/`: 01 ITBI, 02 mobilidade, 03 integração, 04 análise imobiliária e 05 artigo.
- `src/`: módulos utilizados pelos notebooks.
- `data/raw/`: fontes originais, IPCA e manifestos de origem.
- `data/processed/`: bases finais compactadas e camadas geográficas.
- `resultados/`: tabelas de apoio e entradas espaciais reutilizadas.
- `docs/`: metodologia, caminhada, fontes, proposta e contribuições.
- `slides/`: apresentações em PDF dos marcos 2 e 3.

## Executar

Use Python 3.12 ou mais recente. Na raiz do projeto:

```text
python -m pip install -r requirements.txt
```

Abra `notebooks/05_artigo.ipynb` no VS Code/Jupyter e execute as células na ordem.
As bases e os percursos já estão incluídos: não é necessário geocodificar nem
baixar a rede de ruas novamente. O pandas lê os arquivos `.csv.gz` diretamente.
O explorador interativo da seção 5.9 funciona no ambiente local após a execução;
os controles não funcionam na visualização estática do GitHub.

Os notebooks 01–04 documentam as etapas anteriores. Seu fluxo padrão reutiliza
coordenadas e percursos fornecidos. A geração integral dos percursos de caminhada
não está implementada nesses cinco notebooks. Modos opcionais de nova
geocodificação, exemplo OSM e preparação cartográfica exigem dependências e dados
adicionais e podem consultar serviços externos.

Detalhes e limitações: [metodologia](docs/METODOLOGIA.md),
[percursos a pé](docs/CAMINHADA.md), [fontes BRS](docs/FONTES_BRS.md) e
[contexto histórico](docs/FONTES_EVENTOS.md). Dados OpenStreetMap © contribuidores,
sob [ODbL](https://www.openstreetmap.org/copyright).
