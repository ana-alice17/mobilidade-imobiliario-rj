# Pontos BRS: fonte localizada e recorte que os dados permitem

Consulta às fontes: 28 de outubro de 2026. A revisão anterior dispunha apenas
de corredores BRS. Nesta busca foram encontrados **pontos de embarque reais**,
identificados pelo próprio cadastro oficial, inclusive em arquivo de 2024.

## Fonte recomendada para a análise de 2024

O GTFS da Secretaria Municipal de Transportes do Rio foi preservado pela
Transformative Urban Mobility Initiative (TUMI) e está disponível no catálogo
Transport Data Commons (TDC):

- [Catálogo TUMI/TDC — GTFS Rio de Janeiro, 2024](https://portal.transport-data.org/@tumi/gtfs-rio-de-janeiro).
- [Metadados do catálogo em JSON](https://ckan.transport-data.org/api/3/action/package_show?id=gtfs-rio-de-janeiro).
- [Arquivo de 29 de abril de 2024](https://ckan.tdc.prod.datopian.com/dataset/cfbab80c-294d-4c72-8c54-b8c24413037b/resource/28d83b32-8f1a-44d1-a485-3dd4c922faae/download/gtfs-rio-de-janeiro-29-4-2024-zgfw1k.zip).
- Fonte original indicada pelo catálogo: [Data.Rio — GTFS do Rio](https://www.data.rio/datasets/8ffe62ad3b2f42e49814bf941654ea6c/about).

O arquivo local é `data/raw/brs_gtfs_rio_2024_04_29.zip`. Seu SHA-256 é
`66e33afddae7319735ec48d6f35503712abf8fc906c6559a1e269fb112a1416a`.
O tamanho é 25.040.776 bytes. As datas internas de `stops.txt` e `feed_info.txt`
são 29/04/2024. A versão declarada em `feed_info.txt` é **01Q0424**, com editor
**Secretaria Municipal de Transportes**, início de validade 01/01/2024 e fim
31/12/2024. Essa evidência interna confirma que não se trata apenas de arquivo
atual renomeado como histórico.

Há 7.554 paradas no arquivo. Foram selecionadas as **255 paradas cujo nome
começa por BRS**, como “BRS 1,2,3: Beira Mar” e “BRS 2: Passos”. Todos os 255
identificadores e pares de coordenadas são distintos, e todas essas paradas
aparecem em viagens cadastradas em `stop_times.txt`. A seleção usa identificação
textual da fonte; não cria pontos e não seleciona todo ponto de ônibus que esteja
perto de um corredor.

Os pontos selecionados e suas distâncias a pé em 2024 acompanham a entrega em
`data/processed/acesso_2024_caminhada.csv.gz`; a origem, a versão e o checksum do
arquivo estão em `data/raw/brs_gtfs_2024_manifesto.json`.

O catálogo declara licença CC BY-NC 4.0. O trabalho acadêmico deve atribuir a
fonte original SMTR/Data.Rio e a preservação TUMI/TDC.

## O que pode ser respondido sem inventar

Para as perguntas de proximidade, preços e dispersão, é possível calcular a
caminhada até esses pontos e comparar as transações de **2024** com o cadastro
de **abril de 2024**. Esse recorte inclui o BRS nas quatro modalidades sem
usar distância ao corredor como se fosse distância a um embarque.

A validade anual declarada do GTFS não contém a data individual de criação de
cada ponto nem comprova que o cadastro permaneceu idêntico em todos os meses.
Por isso, a formulação correta é “proximidade aos pontos BRS registrados no
GTFS de abril de 2024”. Não se deve escrever que todos os pontos operaram
durante cada dia de 2024, e tampouco retroagir os 255 pontos às vendas de
2011–2023 como se houvesse histórico confirmado.

Essa análise é descritiva. O cadastro não garante que todos os pontos que
funcionavam como BRS usassem esse nome; o conjunto corresponde aos pontos
explicitamente identificados pela fonte. Mudanças de nome e de posição são
possíveis. A rede pedestre utilizada no projeto é contemporânea de 2026,
outra limitação que precisa acompanhar os resultados.

## Cadastro atual consultado como conferência

Também foi consultada a camada oficial de paradas SPPO publicada por
PrefeituraRio, item ArcGIS `fd07613c9a1c45299389c0f7cff8e2a0`:

[Paradas SPPO — serviço oficial](https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Hosted/Rede_%C3%94nibus_SPPO_2_visualiza%C3%A7%C3%A3o/FeatureServer/0).

O filtro `UPPER(stop_name) LIKE '%BRS%'` retornou **253 pontos**, com última
edição informada em 22/10/2026. O cadastro atual ficou preservado em
`data/raw/brs_pontos_oficiais_2026.geojson` e seu manifesto. Ele não substitui
o snapshot de 2024 na comparação principal. A diferença entre os cadastros
é mais uma razão para não presumir que o atual vale para todo o passado.

O endereço do GTFS atual indicado no catálogo oficial,
`https://dados.mobilidade.rio/gtfs/schedule`, respondeu 404 nesta consulta;
o antigo item ArcGIS de download respondeu 403. O arquivo de 2024 preservado
pela TUMI foi obtido e validado normalmente. As respostas de indisponibilidade
não significam inexistência dos dados ou dos serviços de ônibus.
