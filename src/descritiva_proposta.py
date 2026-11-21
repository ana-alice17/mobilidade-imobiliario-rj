"""Respostas descritivas às perguntas de transporte da proposta original.

O módulo oferece o recorte histórico de Metrô, BRT e VLT em 2011–2024 e
o recorte das quatro modalidades em 2024, único ano com cadastro BRS verificável.
Os preços são corrigidos pelo IPCA mensal para reais de dezembro de 2024.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import analises_territoriais as at

RAIZ = Path(__file__).resolve().parents[1]
LIMITE_PERTO = 1000
MODAIS = {"Metrô": "dist_ref_metro_m", "BRT": "dist_ref_brt_m",
          "VLT": "dist_ref_vlt_m", "BRS": "dist_ref_brs_m"}
CORES = {"Metrô": "#2a78d6", "BRT": "#eb6834", "VLT": "#279b3b", "BRS": "#8856a7"}
METRICAS = ["n", "media", "mediana", "q1", "q3", "variancia", "desvio_padrao",
            "minimo", "maximo", "amplitude", "CV", "IIQ"]


def estatisticas(base, chaves=None, coluna="m2_real"):
    """Estatísticas usuais; variância e desvio padrão amostrais (ddof=1)."""
    if not chaves:
        x = pd.to_numeric(base[coluna], errors="raise").dropna()
        q1, q3 = x.quantile([.25, .75])
        return pd.Series(dict(n=len(x), media=x.mean(), mediana=x.median(),
            q1=q1, q3=q3, variancia=x.var(), desvio_padrao=x.std(),
            minimo=x.min(), maximo=x.max(), amplitude=x.max()-x.min(),
            CV=x.std()/x.mean() if len(x) and x.mean()!=0 else np.nan, IIQ=q3-q1))
    agrupado = base.groupby(chaves, observed=True, dropna=False)[coluna]
    t = agrupado.agg(n="count", media="mean", mediana="median", variancia="var",
                    desvio_padrao="std", minimo="min", maximo="max")
    t["q1"] = agrupado.quantile(.25)
    t["q3"] = agrupado.quantile(.75)
    t["amplitude"] = t.maximo-t.minimo
    t["CV"] = t.desvio_padrao/t.media.where(t.media.ne(0))
    t["IIQ"] = t.q3-t.q1
    return t[METRICAS]


def mascara_valida(base, coluna, limite=LIMITE_PERTO):
    """Sem rota nunca vira longe; possível acesso omitido torna longe incerto."""
    valida = np.isfinite(base[coluna]) & base[coluna].ge(0)
    incerta = coluna.removesuffix("_m")+"_acesso_ausente_reta_m"
    if incerta in base:
        valida &= ~(base[coluna].gt(limite) & base[incerta].le(limite))
    return valida


def _territorios(base):
    yield "Cidade", "Rio de Janeiro", base
    for col, nivel in [("bairro", "Bairro"), ("ap", "AP")]:
        for nome, grupo in base.groupby(col, observed=True, dropna=False):
            yield nivel, str(nome) if pd.notna(nome) else "Sem identificação", grupo


def comparar_proximidade(amostra, limite=LIMITE_PERTO, minimo=10):
    """Médias/medianas e dispersão perto/longe, sem modelos ou estratificação.

    As estatísticas são mostradas com suas contagens. O contraste percentual só
    é informado quando há ao menos ``minimo`` transações de cada lado.
    """
    resumos, dispersoes, distancias = [], [], []
    for nivel, territorio, universo in _territorios(amostra):
        for modal, coluna in MODAIS.items():
            valida = mascara_valida(universo, coluna, limite)
            b = universo.loc[valida]
            lados = {"Perto": b.loc[b[coluna].le(limite)], "Longe": b.loc[b[coluna].gt(limite)]}
            p, l = [estatisticas(lados[x]) for x in ["Perto", "Longe"]]
            comparavel = p.n >= minimo and l.n >= minimo
            r = dict(nivel=nivel, territorio=territorio, modalidade=modal, limite_m=limite,
                     n_amostra=len(universo), n_classificaveis=len(b),
                     n_indeterminados=len(universo)-len(b),
                     cobertura_pct=100*len(b)/len(universo) if len(universo) else np.nan,
                     comparavel_minimo=comparavel)
            for nome, valores, g in [("perto", p, lados["Perto"]), ("longe", l, lados["Longe"])]:
                for metrica in METRICAS:
                    r[f"{metrica}_{nome}"] = valores[metrica]
                r[f"locais_{nome}"] = g.id_grupo_geografico.nunique()
            r["diferenca_media_pct"] = 100*(p.media/l.media-1) if comparavel and l.media>0 else np.nan
            r["diferenca_mediana_pct"] = 100*(p.mediana/l.mediana-1) if comparavel and l.mediana>0 else np.nan
            resumos.append(r)
            for nome, g in lados.items():
                valores = estatisticas(g).to_dict()
                dispersoes.append(dict(nivel=nivel, territorio=territorio, modalidade=modal,
                    proximidade=nome, limite_m=limite, locais=g.id_grupo_geografico.nunique(), **valores))
            # É a distância até o acesso cadastrado alcançável; não inclui casos
            # cuja ausência de medida poderia ser confundida com distância longa.
            continua = np.isfinite(universo[coluna]) & universo[coluna].ge(0)
            incerta = coluna.removesuffix('_m')+'_acesso_ausente_reta_m'
            if incerta in universo:
                continua &= ~universo[coluna].gt(universo[incerta])
            x = universo.loc[continua,coluna]
            locais_continuos = universo.loc[continua,'id_grupo_geografico'].nunique()
            suporte = len(x)>=10 and locais_continuos>=3
            distancias.append(dict(nivel=nivel, territorio=territorio, modalidade=modal,
                limite_m=limite, n_amostra=len(universo), n_classificaveis=len(b),
                n_distancia=len(x),locais=locais_continuos,suporte_quantis=suporte,
                mediana_percurso_calculado_m=x.median() if suporte else np.nan,
                media_percurso_calculado_m=x.mean() if suporte else np.nan,
                q1_percurso_m=x.quantile(.25) if suporte else np.nan,
                q3_percurso_m=x.quantile(.75) if suporte else np.nan,
                n_perto=int(p.n), n_longe=int(l.n),
                percentual_perto=100*p.n/len(b) if len(b) else np.nan))
            assert int(p.n+l.n)==len(b)
    return pd.DataFrame(resumos), pd.DataFrame(dispersoes), pd.DataFrame(distancias)


def distribuicoes_comuns(amostra, limite=LIMITE_PERTO):
    validas = pd.DataFrame({m: mascara_valida(amostra,c,limite) for m,c in MODAIS.items()})
    comum = amostra.loc[validas.all(axis=1)].copy()
    proximas = pd.DataFrame({m: comum[c].le(limite) for m,c in MODAIS.items()},index=comum.index)
    tabelas = []
    for modal in MODAIS:
        g = comum.loc[proximas[modal]]
        tabelas.append(dict(modalidade=modal,locais=g.id_grupo_geografico.nunique(),
                           **estatisticas(g).to_dict()))
    distribuicoes = pd.DataFrame(tabelas).set_index("modalidade")
    sobreposicoes = proximas.astype("int64").T@proximas.astype("int64")
    perfis = proximas.apply(lambda r: " + ".join(r.index[r]) or "Nenhuma",axis=1).value_counts().rename("n").to_frame()
    perfis["percentual"] = 100*perfis.n/len(comum) if len(comum) else np.nan
    assert perfis.n.sum()==len(comum)
    np.testing.assert_array_equal(sobreposicoes,sobreposicoes.T)
    np.testing.assert_array_equal(np.diag(sobreposicoes),proximas.sum().to_numpy())
    return comum,proximas,distribuicoes,sobreposicoes,perfis


def figura_distribuicoes(comum, proximas, limite=LIMITE_PERTO, modais=None, periodo="2024"):
    """Pergunta 7: posição, dispersão e forma na mesma amostra."""
    modais = MODAIS if modais is None else modais
    fig, axs = plt.subplots(1,2,figsize=(11,4.2))
    grupos = [comum.loc[proximas[m],"m2_real"].to_numpy() for m in modais]
    caixas = axs[0].boxplot(grupos,tick_labels=list(modais),showfliers=False,
                            whis=(5,95),patch_artist=True)
    for caixa,m in zip(caixas["boxes"],modais):
        caixa.set_facecolor(CORES[m]);caixa.set_alpha(.55)
    axs[0].set_yscale("log")
    axs[0].set(ylabel="R$ de dez/2024 por m² (escala log)",
               title="Preços próximos — caixa: Q1–Q3; hastes: P5–P95")
    for m,x in zip(modais,grupos):
        x=np.sort(x)
        if len(x):
            contagem=f'{len(x):,}'.replace(',','.')
            axs[1].plot(x,np.arange(1,len(x)+1)/len(x),label=f"{m} (n={contagem})",color=CORES[m])
    axs[1].set_xscale("log")
    axs[1].set(xlabel="R$ de dez/2024 por m² (escala log)",ylabel="Proporção acumulada",
               title="Distribuição acumulada dos preços próximos",ylim=(0,1))
    axs[1].legend(fontsize=8)
    formato=mticker.FuncFormatter(lambda v,_:f'{v:,.0f}'.replace(',','.'))
    axs[0].yaxis.set_major_locator(mticker.FixedLocator([1000,2000,3000,5000,10000,20000,50000,100000]))
    axs[0].yaxis.set_major_formatter(formato)
    axs[0].yaxis.set_minor_formatter(mticker.NullFormatter())
    axs[1].xaxis.set_major_locator(mticker.FixedLocator([1000,3000,10000,30000,100000]))
    axs[1].xaxis.set_major_formatter(formato)
    axs[1].xaxis.set_minor_formatter(mticker.NullFormatter())
    for ax in axs:ax.grid(axis="y",alpha=.2)
    fig.suptitle(f"Transações de {periodo} — até {limite} m a pé, na mesma amostra",fontsize=11)
    fig.tight_layout();return fig


def figura_comparacao(resumo, modais=None, periodo="2024"):
    modais = MODAIS if modais is None else modais
    cidade = resumo.loc[resumo.nivel.eq("Cidade")].set_index("modalidade").reindex(modais)
    fig,axs=plt.subplots(1,2,figsize=(10,4.2))
    cidade[["media_perto","media_longe"]].rename(columns={"media_perto":"Perto","media_longe":"Longe"}).plot.bar(ax=axs[0],rot=0,color=["#2a78d6","#a9b7c6"],legend=False)
    cidade[["mediana_perto","mediana_longe"]].rename(columns={"mediana_perto":"Perto","mediana_longe":"Longe"}).plot.bar(ax=axs[1],rot=0,color=["#2a78d6","#a9b7c6"],legend=False)
    for ax,titulo in zip(axs,["Média","Mediana"]):
        ax.set(title=titulo,ylabel="R$ de dez/2024 por m²",xlabel="");ax.grid(axis="y",alpha=.2)
        ax.set_ylim(0, ax.get_ylim()[1]*1.15)
        for cont in ax.containers:
            ax.bar_label(cont, fmt=lambda v: f"{v:,.0f}".replace(",","."), fontsize=7.5, padding=2)
    handles,labels=axs[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(.5,.0))
    lim=int(cidade.limite_m.iloc[0])
    fig.suptitle(f"Preços de {periodo} perto e longe do transporte — limiar de {lim} m")
    fig.tight_layout(rect=(0,.07,1,.94));return fig


def _ler(valor, padrao):
    if isinstance(valor,pd.DataFrame):return valor.copy()
    return pd.read_csv(Path(valor) if valor is not None else padrao,low_memory=False)


def carregar_e_analisar(base=None, referencia=None, pasta=None, limite=LIMITE_PERTO):
    """Lê entradas reais, calcula as respostas e exporta tabelas auditáveis."""
    bruto=_ler(base,RAIZ/'data/processed/itbi_residencial_2011_2024_geocodificado_completo.csv.gz')
    ref=_ler(referencia,RAIZ/'data/processed/acesso_2024_caminhada.csv.gz')
    assert ref.id_grupo_geografico.notna().all() and ref.id_grupo_geografico.is_unique
    faltando=set(MODAIS.values())-set(ref)
    if faltando:raise ValueError(f"Distâncias ausentes: {sorted(faltando)}")
    for c in MODAIS.values():
        ref[c]=pd.to_numeric(ref[c],errors="raise")
        assert ref.loc[np.isfinite(ref[c]),c].ge(0).all()
    universo=at.preparar_territorios(bruto.loc[bruto.ano.eq(2024)&at.filtro_precos(bruto)].copy())
    espacial=universo.loc[universo.qualidade_geocodificacao.eq("alta_precisao")].copy()
    # Reutilizar a rota só é válido se o identificador ainda localizar o mesmo
    # ponto; preços e atributos vêm sempre da base atual, não do cache espacial.
    pos=ref.set_index('id_grupo_geografico').reindex(espacial.id_grupo_geografico)
    for coluna in ['lat_analise','lon_analise']:
        np.testing.assert_allclose(pos[coluna].to_numpy(),espacial[coluna].to_numpy(),rtol=0,atol=1e-10)
    campos=[c for c in ref if c.startswith("dist_ref_")]
    amostra=espacial.merge(ref[["id_grupo_geografico",*campos]],on="id_grupo_geografico",how="left",validate="many_to_one")
    assert len(amostra)==len(espacial) and amostra.id_transacao.is_unique
    resumo,disp,dist=comparar_proximidade(amostra,limite)
    comum,proximas,distrib,sobre,perfis=distribuicoes_comuns(amostra,limite)
    cob=at.cobertura_geocodificacao(universo,amostra)
    cenarios=[]
    for lim in [500,800,1000,1500]:
        # O panorama da cidade é suficiente para a checagem do limiar. A análise
        # principal mantém as tabelas completas por bairro e AP.
        for modal,c in MODAIS.items():
            v=mascara_valida(amostra,c,lim)
            p=amostra.loc[v&amostra[c].le(lim)];l=amostra.loc[v&amostra[c].gt(lim)]
            cenarios.append(dict(modalidade=modal,limite_m=lim,n_classificaveis=int(v.sum()),
                n_perto=len(p),n_longe=len(l),media_perto=p.m2_real.mean(),media_longe=l.m2_real.mean(),
                mediana_perto=p.m2_real.median(),mediana_longe=l.m2_real.median(),
                percentual_perto=100*len(p)/v.sum() if v.any() else np.nan))
    sens=pd.DataFrame(cenarios)
    for _,g in sens.groupby('modalidade'):
        assert g.sort_values('limite_m').n_perto.is_monotonic_increasing
        assert (g.n_perto+g.n_longe).eq(g.n_classificaveis).all()
    destino=Path(pasta) if pasta is not None else RAIZ/'resultados/proposta'
    destino.mkdir(parents=True,exist_ok=True)
    for nome,t,index in [('resumo_proximidade',resumo,False),('estatisticas_proximidade',disp,False),
        ('distancias_territorio',dist,False),('cobertura_geocodificacao',cob,False),
        ('distribuicoes_modal',distrib,True),('sobreposicoes',sobre,True),
        ('perfis',perfis,True),('sensibilidade_limites',sens,False)]:
        t.to_csv(destino/(nome+'.csv'),index=index)
    manifesto=dict(ano_transacoes=2024,limite_principal_m=limite,
        universo_precos_2024=len(universo),amostra_espacial_2024=len(amostra),
        amostra_comum_quatro_modalidades=len(comum),modais=MODAIS,
        definicao=f'Perto: percurso estimado até o acesso cadastrado de até {limite} m; longe: percurso maior entre classificáveis.',
        limite_historico='Cadastro BRS de 2024 não retroagido. Rede pedestre contemporânea aplicada às transações de 2024.',
        comparacoes='Descritivas. O complemento aproxima o perfil por distância com duas curvas.',
        unidade='Reais de dezembro de 2024 por m²; variância em (R$/m²)².')
    (destino/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2),encoding='utf-8')
    return dict(universo_2024=universo,amostra_2024=amostra,cobertura=cob,
        resumo_proximidade=resumo,estatisticas_proximidade=disp,distancias_territorio=dist,
        comum=comum,proximas=proximas,distribuicoes_modal=distrib,sobreposicoes=sobre,
        perfis=perfis,sensibilidade=sens,manifesto=manifesto)




# ---------------------------------------------------------------------------
# Recorte histórico (2011–2024) para Metrô, BRT e VLT; BRS fica em 2024.
# Reutiliza os percursos a pé já calculados em itbi_com_caminhada.csv.gz.
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
MODAIS_H = {"Metrô": "dist_walk_metro_m", "BRT": "dist_walk_brt_m", "VLT": "dist_walk_vlt_m"}
PERIODO_H = "2011–2024"


def carregar_historico():
    base = pd.read_csv(RAIZ/'data/processed/itbi_com_caminhada.csv.gz', low_memory=False)
    assert base.id_transacao.is_unique
    assert base.qualidade_geocodificacao.eq('alta_precisao').all()
    return at.preparar_territorios(base.loc[at.filtro_precos(base)].copy())



def comparar_proximidade_h(amostra, limite=LIMITE_PERTO, minimo=10):
    """Médias/medianas e dispersão perto/longe por modalidade, bairro e AP."""
    resumos, dispersoes, distancias = [], [], []
    for nivel, territorio, universo in _territorios(amostra):
        for modal, coluna in MODAIS_H.items():
            valida = at.mascara_distancia(universo, coluna, limite)
            b = universo.loc[valida]
            lados = {"Perto": b.loc[b[coluna].le(limite)], "Longe": b.loc[b[coluna].gt(limite)]}
            p, l = [estatisticas(lados[x]) for x in ["Perto", "Longe"]]
            comparavel = p.n >= minimo and l.n >= minimo
            r = dict(nivel=nivel, territorio=territorio, modalidade=modal, limite_m=limite,
                     periodo=PERIODO_H, n_amostra=len(universo), n_classificaveis=len(b),
                     n_indeterminados=len(universo)-len(b),
                     cobertura_pct=100*len(b)/len(universo) if len(universo) else np.nan,
                     comparavel_minimo=comparavel)
            for nome, valores, g in [("perto", p, lados["Perto"]), ("longe", l, lados["Longe"])]:
                for metrica in METRICAS:
                    r[f"{metrica}_{nome}"] = valores[metrica]
                r[f"locais_{nome}"] = g.id_grupo_geografico.nunique()
            r["diferenca_media_pct"] = 100*(p.media/l.media-1) if comparavel and l.media > 0 else np.nan
            r["diferenca_mediana_pct"] = 100*(p.mediana/l.mediana-1) if comparavel and l.mediana > 0 else np.nan
            resumos.append(r)
            for nome, g in lados.items():
                valores = estatisticas(g).to_dict()
                dispersoes.append(dict(nivel=nivel, territorio=territorio, modalidade=modal,
                    proximidade=nome, limite_m=limite, periodo=PERIODO_H,
                    locais=g.id_grupo_geografico.nunique(), **valores))
            continua = at.mascara_distancia_continua(universo, coluna)
            x = universo.loc[continua, coluna]
            locais_continuos = universo.loc[continua, 'id_grupo_geografico'].nunique()
            suporte = len(x) >= 10 and locais_continuos >= 3
            distancias.append(dict(nivel=nivel, territorio=territorio, modalidade=modal,
                limite_m=limite, periodo=PERIODO_H, n_amostra=len(universo), n_classificaveis=len(b),
                n_distancia=len(x), locais=locais_continuos, suporte_quantis=suporte,
                mediana_percurso_calculado_m=x.median() if suporte else np.nan,
                media_percurso_calculado_m=x.mean() if suporte else np.nan,
                q1_percurso_m=x.quantile(.25) if suporte else np.nan,
                q3_percurso_m=x.quantile(.75) if suporte else np.nan,
                n_perto=int(p.n), n_longe=int(l.n),
                percentual_perto=100*p.n/len(b) if len(b) else np.nan))
            assert int(p.n+l.n) == len(b)
    return pd.DataFrame(resumos), pd.DataFrame(dispersoes), pd.DataFrame(distancias)


def distribuicoes_comuns_h(amostra, limite=LIMITE_PERTO):
    """Amostra comum às três modalidades no período completo."""
    validas = pd.DataFrame({m: at.mascara_distancia(amostra, c, limite) for m, c in MODAIS_H.items()})
    comum = amostra.loc[validas.all(axis=1)].copy()
    proximas = pd.DataFrame({m: comum[c].le(limite) for m, c in MODAIS_H.items()}, index=comum.index)
    tabelas = []
    for modal in MODAIS_H:
        g = comum.loc[proximas[modal]]
        tabelas.append(dict(modalidade=modal, locais=g.id_grupo_geografico.nunique(),
                            **estatisticas(g).to_dict()))
    distribuicoes = pd.DataFrame(tabelas).set_index("modalidade")
    sobreposicoes = proximas.astype("int64").T@proximas.astype("int64")
    perfis = proximas.apply(lambda r: " + ".join(r.index[r]) or "Nenhuma", axis=1).value_counts().rename("n").to_frame()
    perfis["percentual"] = 100*perfis.n/len(comum) if len(comum) else np.nan
    assert perfis.n.sum() == len(comum)
    np.testing.assert_array_equal(sobreposicoes, sobreposicoes.T)
    np.testing.assert_array_equal(np.diag(sobreposicoes), proximas.sum().to_numpy())
    return comum, proximas, distribuicoes, sobreposicoes, perfis


def sensibilidade_h(amostra):
    cenarios = []
    for lim in [500, 800, 1000, 1500]:
        for modal, c in MODAIS_H.items():
            v = at.mascara_distancia(amostra, c, lim)
            p = amostra.loc[v & amostra[c].le(lim)]
            l = amostra.loc[v & amostra[c].gt(lim)]
            cenarios.append(dict(modalidade=modal, limite_m=lim, periodo=PERIODO_H,
                n_classificaveis=int(v.sum()), n_perto=len(p), n_longe=len(l),
                media_perto=p.m2_real.mean(), media_longe=l.m2_real.mean(),
                mediana_perto=p.m2_real.median(), mediana_longe=l.m2_real.median(),
                percentual_perto=100*len(p)/v.sum() if v.any() else np.nan))
    sens = pd.DataFrame(cenarios)
    for _, g in sens.groupby('modalidade'):
        assert g.sort_values('limite_m').n_perto.is_monotonic_increasing
        assert (g.n_perto+g.n_longe).eq(g.n_classificaveis).all()
    return sens


def composicao_ap_h(amostra, limite=LIMITE_PERTO):
    """Composição do grupo perto por AP e nível de preço de cada AP.

    Mostra onde os acessos de cada modalidade se refletem nas vendas:
    o grupo perto do VLT concentra-se no Centro, o do Metrô na Zona Sul,
    o do BRT nas zonas Norte e Oeste.
    """
    linhas = []
    for modal, coluna in MODAIS_H.items():
        b = amostra.loc[at.mascara_distancia(amostra, coluna, limite)]
        perto = b.loc[b[coluna].le(limite)]
        cont = perto.ap.value_counts()
        for ap, n in cont.items():
            linhas.append(dict(modalidade=modal, ap=str(ap), n_perto=int(n),
                               pct_perto=100*n/len(perto) if len(perto) else np.nan,
                               total_perto=len(perto)))
    comp = pd.DataFrame(linhas)
    med_ap = (amostra.groupby('ap', observed=True).m2_real
              .agg(mediana='median', n='size').reset_index())
    med_ap['ap'] = med_ap.ap.astype(str)
    return comp, med_ap


def carregar_e_analisar_h(pasta=None, limite=LIMITE_PERTO):
    from preco_por_distancia import comparacoes_estratificadas
    amostra = carregar_historico()
    resumo, disp, dist = comparar_proximidade_h(amostra, limite)
    comum, proximas, distrib, sobre, perfis = distribuicoes_comuns_h(amostra, limite)
    sens = sensibilidade_h(amostra)
    tres = comparacoes_estratificadas(amostra, limite, modais=MODAIS_H, mascara=at.mascara_distancia)
    comp, med_ap = composicao_ap_h(amostra, limite)
    destino = Path(pasta) if pasta is not None else RAIZ/'resultados/historico'
    destino.mkdir(parents=True, exist_ok=True)
    for nome, t, index in [('resumo_proximidade', resumo, False), ('estatisticas_proximidade', disp, False),
        ('distancias_territorio', dist, False), ('distribuicoes_modal', distrib, True),
        ('sobreposicoes', sobre, True), ('perfis', perfis, True), ('sensibilidade_limites', sens, False),
        ('comparacoes_estratificadas', tres, True), ('composicao_ap', comp, False), ('mediana_ap', med_ap, False)]:
        t.to_csv(destino/(nome+'.csv'), index=index)
    manifesto = dict(periodo=PERIODO_H, limite_principal_m=limite, modais=MODAIS_H,
        n_amostra=len(amostra), amostra_comum_tres_modalidades=len(comum),
        janelas='BRT a partir de 2013 e VLT a partir de 2017 (ano seguinte à inauguração cadastrada); Metrô todo o período.',
        brs='Fora deste recorte: cadastro verificável apenas em 2024 (descritiva_proposta).',
        definicao=f'Perto: percurso a pé até o acesso de até {limite} m; longe: percurso maior entre classificáveis.',
        unidade='Reais de dezembro de 2024 por m²; variância em (R$/m²)².')
    (destino/'manifesto.json').write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding='utf-8')
    return dict(amostra=amostra, resumo_proximidade=resumo, estatisticas_proximidade=disp,
        distancias_territorio=dist, comum=comum, proximas=proximas, distribuicoes_modal=distrib,
        sobreposicoes=sobre, perfis=perfis, sensibilidade=sens, estratificadas=tres,
        composicao_ap=comp, mediana_ap=med_ap, manifesto=manifesto)


def figura_composicao(comp, med_ap, extras=None):
    """Onde estão as vendas perto de cada modalidade e o preço de cada AP.

    Barras empilhadas: participação de cada AP no grupo perto. Painel direito:
    mediana de preço da AP, na mesma ordem (da mais barata à mais cara).
    """
    import matplotlib.pyplot as plt
    med_ap = med_ap.copy()
    med_ap['ap'] = med_ap.ap.astype(str)
    ordem_ap = med_ap.sort_values('mediana').ap.tolist()
    rotulos = {ap: ap.replace(' · ', ' – ') for ap in ordem_ap}
    mods = list(dict.fromkeys(comp.modalidade.tolist()))
    if extras:
        mods = mods + [m for m in extras if m not in mods]
    cmap = plt.get_cmap('cividis')
    cores_ap = {ap: cmap(i / max(len(ordem_ap) - 1, 1)) for i, ap in enumerate(ordem_ap)}
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={'width_ratios': [2.3, 1]})
    yy = np.arange(len(mods))[::-1]
    series = {}
    for m in mods:
        if m in set(comp.modalidade):
            series[m] = comp.loc[comp.modalidade.eq(m)].set_index('ap').pct_perto
        else:
            series[m] = extras[m]
    for y0, m in zip(yy, mods):
        g = series[m]
        left = 0.0
        for ap in ordem_ap:
            v = float(g.get(ap, 0.0)) if pd.notna(g.get(ap, np.nan)) else 0.0
            if v > 0:
                axs[0].barh(y0, v, left=left, color=cores_ap[ap], height=.62, edgecolor='white', linewidth=.5)
                if v >= 7:
                    axs[0].text(left + v / 2, y0, f'{v:.0f}%', ha='center', va='center', fontsize=8, color='white')
            left += v
    axs[0].set_yticks(yy, mods)
    axs[0].set_xlim(0, 100)
    axs[0].set_xlabel('Participação no grupo perto (%)')
    axs[0].set_title('Em que Área de Planejamento estão as vendas perto do acesso')
    axs[0].grid(axis='x', alpha=.2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cores_ap[ap]) for ap in ordem_ap]
    axs[0].legend(handles, [rotulos[ap] for ap in ordem_ap], loc='upper center',
                  bbox_to_anchor=(.5, -.18), ncol=3, frameon=False, fontsize=8)
    med = med_ap.set_index('ap').mediana
    yay = np.arange(len(ordem_ap))
    axs[1].barh(yay, [med[ap] for ap in ordem_ap], color=[cores_ap[ap] for ap in ordem_ap], height=.62)
    for y0, ap in zip(yay, ordem_ap):
        axs[1].text(med[ap], y0, f'  R$ {med[ap]:,.0f}'.replace(',', '.'), va='center', fontsize=8)
    axs[1].set_yticks(yay, [rotulos[ap].split(' – ')[0] for ap in ordem_ap])
    axs[1].set_xlim(0, med.max() * 1.28)
    axs[1].set_xlabel('Mediana do preço (R$/m², dez/2024)')
    axs[1].set_title('Preço mediano de cada AP')
    axs[1].grid(axis='x', alpha=.2)
    fig.tight_layout()
    return fig


if __name__=='__main__':
    r=carregar_e_analisar()
    print(r['resumo_proximidade'].loc[lambda x:x.nivel.eq('Cidade'),
        ['modalidade','n_perto','n_longe','media_perto','media_longe','mediana_perto','mediana_longe']].to_string(index=False))
