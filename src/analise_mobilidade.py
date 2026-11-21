"""Cálculos descritivos compartilhados pelos notebooks 03 e 05."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

MODAIS = {"Metrô": "dist_metro_m", "BRT": "dist_brt_m", "VLT": "dist_vlt_m", "BRS (corredor)": "dist_brs_m"}
CHAVES = ["nm_bairro_norm", "ano", "ds_imovel_tipologia"]

# Mesma aproximação anual interpolada usada no notebook 04; não é a série mensal oficial.
IPCA = {2011: 6.50, 2012: 5.84, 2013: 5.91, 2014: 6.41, 2015: 10.67, 2016: 6.29,
        2017: 2.95, 2018: 3.75, 2019: 4.31, 2020: 4.52, 2021: 10.06,
        2022: 5.79, 2023: 4.62, 2024: 4.83}

def corrigir_ipca_aproximado(base):
    indice_dez = {2010: 1.0}
    for ano, taxa in IPCA.items():
        indice_dez[ano] = indice_dez[ano - 1] * (1 + taxa / 100)
    if not (base.ano.between(2011, 2024) & base.mes.between(1, 12)
            & base.ano.mod(1).eq(0) & base.mes.mod(1).eq(0)).all():
        raise ValueError("Ano ou mês inválido para correção monetária.")
    indice = np.array([indice_dez[int(a)-1] * (1+IPCA[int(a)]/100)**(m/12)
                       for a, m in zip(base.ano, base.mes)])
    return base.valor_m2 * indice_dez[2024] / indice

def corrigir_ipca(base):
    """Poder de compra do mês observado em reais de dez/2024, SIDRA 1737.

    Usa o número-índice do próprio mês (convenção de fim de mês), não uma
    calculadora de contrato que inclui a inflação do mês inicial inteiro.
    Ausência de mês oficial é erro: não há fallback silencioso à interpolação.
    """
    arquivo = Path(__file__).resolve().parents[1]/'data/raw/ipca_sidra_1737.json'
    serie = json.loads(arquivo.read_text(encoding='utf-8-sig'))[1:]
    indices = {int(r['D3C']): float(r['V']) for r in serie}
    anos = pd.to_numeric(base.ano, errors='coerce')
    meses = pd.to_numeric(base.mes, errors='coerce')
    if not (anos.between(2011,2024) & meses.between(1,12)
            & anos.mod(1).eq(0) & meses.mod(1).eq(0)).all():
        raise ValueError('Ano/mês inválido para IPCA mensal.')
    chaves = (100*anos+meses).astype(int)
    indice = chaves.map(indices)
    if indice.isna().any() or not indice.gt(0).all():
        raise ValueError('Série IPCA oficial incompleta.')
    return base.valor_m2 * indices[202412]/indice

def preparar(dados):
    dados = dados.copy()
    obrigatorias = set(CHAVES + ["mes", "area", "valor_m2", "valor_m2_suspeito", *MODAIS.values()])
    if obrigatorias - set(dados):
        raise ValueError(f"Colunas ausentes: {sorted(obrigatorias - set(dados))}")
    for col in ["area", "valor_m2", "ano", "mes", *MODAIS.values()]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")
    if "id_transacao" in dados and (dados.id_transacao.isna().any() or not dados.id_transacao.is_unique):
        raise ValueError("Identificadores de transação ausentes ou duplicados.")
    flag = dados.valor_m2_suspeito.astype(str).str.strip().str.lower()
    if not flag.isin(["true", "false"]).all():
        raise ValueError("Sinalização de preços ausente ou inválida.")
    dados["valor_m2_suspeito"] = flag.eq("true")
    validos = np.isfinite(dados.valor_m2) & dados.valor_m2.gt(0)
    # Preserva-se a seleção espacial da integração; o critério de preço é o do notebook 04.
    amostra = dados.loc[validos & ~dados.valor_m2_suspeito].copy()
    amostra["m2_real"] = corrigir_ipca(amostra)
    return dados, amostra

def distancia_valida(df, col, limite=500):
    valida = np.isfinite(df[col]) & df[col].ge(0)
    sem_ano = col.removesuffix("_m") + "_sem_ano_m"
    if sem_ano in df:
        # Sem data, não se pode declarar longe um imóvel potencialmente próximo.
        valida &= ~(df[col].gt(limite) & df[sem_ano].le(limite))
    return valida

def comparar(amostra, limite=500, minimo=10):
    resultados, detalhes = [], {}
    for modal in MODAIS:
        col = MODAIS[modal]
        base = amostra.loc[distancia_valida(amostra,col,limite)].copy()
        base["perto"] = base[col].le(limite)
        completa = base.dropna(subset=CHAVES)
        for chave in ["nm_bairro_norm", "ds_imovel_tipologia"]:
            completa = completa.loc[completa[chave].astype(str).str.strip().ne("")]
        agregado = completa.groupby(CHAVES + ["perto"]).m2_real.agg(n="size", mediana="median")
        n = agregado.n.unstack("perto").reindex(columns=[False,True],fill_value=0).fillna(0)
        med = agregado.mediana.unstack("perto").reindex(columns=[False,True])
        g = pd.DataFrame({"n_longe":n[False], "n_perto":n[True],
                          "mediana_longe":med[False], "mediana_perto":med[True]})
        g = g.loc[g.n_longe.ge(minimo)&g.n_perto.ge(minimo)].copy()
        g["diferenca_pct"] = 100*(g.mediana_perto/g.mediana_longe-1)
        detalhes[modal] = g
        geral = base.groupby("perto").m2_real.median().reindex([False,True])
        medias = base.groupby("perto").m2_real.mean().reindex([False, True])
        incluidos = int(g[["n_longe","n_perto"]].to_numpy().sum())
        resultados.append(dict(modalidade=modal,n_amostra=len(amostra),n_distancia_valida=len(base),
            n_chaves_completas=len(completa),grupos_avaliados=len(n),grupos_comparaveis=len(g),
            cobertura_grupos_pct=100*len(g)/len(n) if len(n) else np.nan,
            n_transacoes_comparaveis=incluidos,
            cobertura_amostra_pct=100*incluidos/len(amostra) if len(amostra) else np.nan,
            cobertura_distancia_valida_pct=100*incluidos/len(base) if len(base) else np.nan,
            media_geral_longe=medias[False],media_geral_perto=medias[True],
            mediana_geral_longe=geral[False],mediana_geral_perto=geral[True],
            diferenca_geral_pct=100*(geral[True]/geral[False]-1),
            mediana_diferencas_grupos_pct=g.diferenca_pct.median()))
    return pd.DataFrame(resultados), detalhes

def tabela_artigo(resumo):
    tabela = resumo.set_index("modalidade")[["diferenca_geral_pct","mediana_diferencas_grupos_pct",
        "grupos_comparaveis","n_transacoes_comparaveis","cobertura_amostra_pct"]].rename(columns={
        "diferenca_geral_pct":"Diferença geral (%)", "mediana_diferencas_grupos_pct":"Diferença por grupo¹ (%)",
        "grupos_comparaveis":"Grupos", "n_transacoes_comparaveis":"Transações", "cobertura_amostra_pct":"Cobertura² (%)"})
    tabela.index.name="Modalidade"
    return tabela.round(2)

def evolucao_proximidade(dados):
    proporcao = pd.DataFrame(index=sorted(dados.ano.dropna().unique()))
    denominadores = pd.DataFrame(index=proporcao.index)
    for modal,col in MODAIS.items():
        validas = dados.loc[distancia_valida(dados,col)]
        denominadores[modal] = validas.groupby("ano").size().reindex(proporcao.index,fill_value=0)
        proporcao[modal] = validas[col].le(500).groupby(validas.ano).mean()*100
    proporcao.index.name=denominadores.index.name="Ano"
    return proporcao,denominadores

def figura_proximidade(proporcao):
    fig,ax=plt.subplots(figsize=(8,3.4))
    proporcao.plot(ax=ax,marker="o",markersize=3)
    ax.set(xlabel="Ano",ylabel="Transações com distância válida (%)",
           title="Transações a até 500 m — estações e corredor BRS")
    ax.grid(axis="y",alpha=.2)
    fig.tight_layout()
    return fig

def figura_comparacao(resumo):
    fig,eixos=plt.subplots(1,2,figsize=(9,3.5))
    tabela=resumo.set_index("modalidade")
    tabela[["diferenca_geral_pct","mediana_diferencas_grupos_pct"]].rename(columns={
        "diferenca_geral_pct":"Geral", "mediana_diferencas_grupos_pct":"Por grupo¹"}).plot.bar(ax=eixos[0],rot=0)
    eixos[0].set(title="Diferenças entre medianas",ylabel="Diferença (%)",xlabel="")
    eixos[0].axhline(0,color="black",linewidth=.7)
    tabela[["cobertura_amostra_pct","cobertura_grupos_pct"]].rename(columns={
        "cobertura_amostra_pct":"Transações²", "cobertura_grupos_pct":"Grupos³"}).plot.bar(ax=eixos[1],rot=0)
    eixos[1].set(title="Cobertura da comparação",ylabel="Cobertura (%)",xlabel="",ylim=(0,100))
    for ax in eixos:
        ax.grid(axis="y",alpha=.2)
        ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def tabela_niveis(resumo):
    return resumo.set_index("modalidade")[["media_geral_longe", "media_geral_perto",
        "mediana_geral_longe", "mediana_geral_perto"]].rename(columns={
        "media_geral_longe": "Média longe", "media_geral_perto": "Média perto",
        "mediana_geral_longe": "Mediana longe", "mediana_geral_perto": "Mediana perto"}).round(2)

def dispersao(amostra, limite=500):
    tabelas = []
    for modal, col in MODAIS.items():
        base = amostra.loc[distancia_valida(amostra, col, limite)].copy()
        base["proximidade"] = np.where(base[col].le(limite), "Perto", "Longe")
        tab = base.groupby("proximidade").m2_real.agg(
            n="size", mediana="median", media="mean", variancia="var", desvio_padrao="std",
            q1=lambda x: x.quantile(.25), q3=lambda x: x.quantile(.75),
            minimo="min", maximo="max")
        tab["IIQ"] = tab.q3 - tab.q1
        tab["amplitude"] = tab.maximo - tab.minimo
        tab["CV"] = tab.desvio_padrao / tab.media
        tab["modalidade"] = modal
        tabelas.append(tab.reset_index())
    return pd.concat(tabelas, ignore_index=True).set_index(["modalidade", "proximidade"])

def formatar_tabela(tabela):
    def formato(v, inteiro=False):
        if pd.isna(v): return "—"
        if isinstance(v, str): return v
        if isinstance(v, (bool, np.bool_)): return 'Sim' if v else 'Não'
        return (f"{v:,.0f}" if inteiro else f"{v:,.2f}").translate(str.maketrans({",": ".", ".": ","}))
    out = tabela.copy().astype(object)
    for c in tabela:
        inteiro = c in ["Grupos", "Transações", "n", "transacoes", "locais", "n_transacoes", "estratos"] or str(c).startswith(("grupos", "n_", "estratos_", "locais_")) or pd.api.types.is_integer_dtype(tabela[c])
        out[c] = tabela[c].map(lambda v: formato(v, inteiro))
    rotulos = {'n':'Transações','media':'Média','mediana':'Mediana','q1':'Q1','q3':'Q3',
        'variancia':'Variância','desvio_padrao':'Desvio padrão','amplitude':'Amplitude',
        'grupos':'Grupos','grupos_razao_definida':'Grupos com razão definida',
        'razao_IIQ_mediana':'Mediana da razão IIQ perto/longe','n_transacoes':'Transações',
        'cobertura_pct':'Cobertura (%)','desvio_mediano_pct':'Desvio mediano (%)',
        'q1_log':'Q1 (log)','q3_log':'Q3 (log)','transacoes':'Transações','pct':'Percentual (%)',
        'locais':'Locais','maior_local_pct':'Maior local (%)','dez_maiores_pct':'10 maiores locais (%)'}
    rotulos.update({'n_classificaveis':'Classificáveis','n_amostra':'Amostra',
        'cobertura_estratos_pct':'Cobertura dos estratos (%)','n_perto':'Perto (n)',
        'n_longe':'Longe (n)','mediana_perto':'Mediana perto','mediana_longe':'Mediana longe',
        'media_perto':'Média perto','media_longe':'Média longe',
        'diferenca_agregada_pct':'Diferença agregada (%)',
        'diferenca_estratos_pct':'Diferença nos estratos (%)','estratos':'Estratos',
        'n_distancia':'Com percurso (n)','mediana_m':'Mediana (m)','p25_m':'Q1 (m)',
        'p75_m':'Q3 (m)','perto_800m_pct':'Até 800 m (%)',
        'n_distancia_continua_identificada':'Mínimo identificável (n)',
        'cobertura_continua_identificada_pct':'Mínimo identificável (%)',
        'mediana_diferencas_estratos_pct':'Diferença nos estratos (%)',
        'estratos_comparaveis':'Estratos comparáveis','iiq_perto':'IIQ perto',
        'iiq_longe':'IIQ longe','mediana_razao_iiq':'Razão IIQ (estratos)',
        'estratos_iiq_definido':'Estratos com razão de IIQ',
        'razao_iiq_estratos':'Razão IIQ (estratos)','n_em_estratos':'Transações nos estratos',
        'diferenca_pct':'Diferença (%)','n_universo':'Universo (n)','n_espacial':'Amostra espacial (n)',
        'cobertura_espacial_pct':'Cobertura espacial (%)',
        'diferenca_mediana_selecao_pct':'Diferença mediana seleção (%)',
        'mediana_universo':'Mediana do universo','mediana_espacial':'Mediana espacial',
        'mediana_bruta_real_pct':'Variação mediana real (%)',
        'indice_composicao_fixa_pct':'Variação composição fixa (%)',
        'volume_por_mes_pct':'Variação registros/mês (%)',
        'cobertura_painel_antes_pct':'Cobertura inicial (%)',
        'cobertura_painel_depois_pct':'Cobertura final (%)',
        'minimo':'Mínimo','maximo':'Máximo','comparavel_minimo':'Pelo menos 10 por lado?',
        'mediana_percurso_calculado_m':'Mediana do percurso (m)',
        'media_percurso_calculado_m':'Média do percurso (m)',
        'q1_percurso_m':'Q1 do percurso (m)','q3_percurso_m':'Q3 do percurso (m)',
        'percentual_perto':'Próximos (%)','n_antes':'Transações iniciais',
        'n_depois':'Transações finais'})
    out=out.rename(columns=rotulos)
    cenarios={'bairro_ano_tipo':'Bairro, ano e tipo',
        'bairro_ano_tipo_area_semestre':'Bairro, ano, tipo, área e semestre',
        'sem_copias_candidatas':'Sem cópias candidatas'}
    if isinstance(out.index,pd.MultiIndex):
        idx=out.index.to_frame(index=False)
        for nome in idx:idx[nome]=idx[nome].map(lambda v:cenarios.get(v,v) if isinstance(v,str) else v)
        out.index=pd.MultiIndex.from_frame(idx)
    out.index.names=[{'modalidade':'Modalidade','proximidade':'Proximidade','ano':'Ano',
        'territorio':'Território','cenario':'Cenário','limite':'Limiar (m)',
        'limite_m':'Limiar (m)','nivel':'Divisão territorial',
        'ano_antes':'Ano inicial','ano_depois':'Ano final'}.get(x,x) for x in out.index.names]
    return out
