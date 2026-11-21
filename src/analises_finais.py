"""Distribuições, dispersão por grupo, evolução e sensibilidade das oito perguntas."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from analise_mobilidade import MODAIS, CHAVES, distancia_valida, comparar, corrigir_ipca


def estatisticas(base, chaves):
    tab = base.groupby(chaves, observed=True).m2_real.agg(
        n='size', media='mean', mediana='median', variancia='var', desvio_padrao='std',
        q1=lambda x: x.quantile(.25), q3=lambda x: x.quantile(.75),
        minimo='min', maximo='max')
    tab['IIQ'] = tab.q3-tab.q1
    tab['amplitude'] = tab.maximo-tab.minimo
    tab['CV'] = tab.desvio_padrao/tab.media
    return tab


def dispersao_por_grupo(amostra, limite=500, minimo=10):
    linhas = []
    for modal, col in MODAIS.items():
        b = amostra.loc[distancia_valida(amostra,col,limite)].dropna(subset=CHAVES).copy()
        for chave in CHAVES:
            b=b.loc[b[chave].astype(str).str.strip().ne('')]
        b['perto'] = b[col].le(limite)
        tab = estatisticas(b, CHAVES+['perto'])
        n=tab.n.unstack('perto').reindex(columns=[False,True]).fillna(0)
        iiq=tab.IIQ.unstack('perto').reindex(columns=[False,True])
        elegivel=n[False].ge(minimo)&n[True].ge(minimo)
        definida=elegivel & iiq[False].gt(0)
        razoes=iiq.loc[definida,True]/iiq.loc[definida,False]
        linhas.append(dict(modalidade=modal, grupos=int(elegivel.sum()),
            grupos_razao_definida=int(definida.sum()), razao_IIQ_mediana=razoes.median(),
            n_transacoes=int(n.loc[elegivel].to_numpy().sum()),
            cobertura_pct=100*n.loc[elegivel].to_numpy().sum()/len(amostra)))
    return pd.DataFrame(linhas).set_index('modalidade')


def distribuicoes(amostra, limite=500):
    validas = pd.DataFrame({m: distancia_valida(amostra,c,limite) for m,c in MODAIS.items()})
    # Mesmos anos e transações potencialmente classificáveis nas quatro modalidades.
    comum = amostra.loc[validas.all(axis=1)].copy()
    proximas = pd.DataFrame({m:comum[c].le(limite) for m,c in MODAIS.items()},index=comum.index)
    longa=[]
    for modal in MODAIS:
        b=comum.loc[proximas[modal],['m2_real',*CHAVES]].copy()
        b['modalidade']=modal
        longa.append(b)
    longa=pd.concat(longa,ignore_index=True)
    resumo=estatisticas(longa,'modalidade').reindex(MODAIS)
    resumo['cobertura_comum_pct']=100*resumo.n/len(comum)
    intersecoes=proximas.astype('int64').T@proximas.astype('int64')
    # Cada perfil conta uma transação uma única vez.
    perfis=proximas.apply(lambda r:' + '.join(r.index[r]) or 'Nenhuma',axis=1)
    contagens=perfis.value_counts().rename('transacoes').to_frame()
    contagens['pct']=100*contagens.transacoes/len(comum)
    comum['log_preco']=np.log(comum.m2_real)
    agr=comum.groupby(CHAVES,observed=True)
    n=agr.m2_real.transform('size')
    referencia=agr.log_preco.transform('median')
    comum['desvio_log']=comum.log_preco-referencia
    linhas=[]
    for modal in MODAIS:
        b=comum.loc[proximas[modal]&n.ge(20)]
        linhas.append(dict(modalidade=modal,n=len(b),
            desvio_mediano_pct=100*np.expm1(b.desvio_log.median()),
            q1_log=b.desvio_log.quantile(.25),q3_log=b.desvio_log.quantile(.75)))
    padronizado=pd.DataFrame(linhas).set_index('modalidade')
    return comum,proximas,longa,resumo,intersecoes,contagens,padronizado


def figura_distribuicoes(longa):
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    grupos=[longa.loc[longa.modalidade.eq(m),'m2_real'].to_numpy() for m in MODAIS]
    axs[0].boxplot(grupos,tick_labels=list(MODAIS),showfliers=False,whis=(5,95))
    axs[0].set_yscale('log')
    axs[0].set(ylabel='R$ de dez/2024 por m² (escala log)',title='Preços próximos: quartis e percentis 5–95')
    axs[0].tick_params(axis='x',labelrotation=18)
    for modal,x in zip(MODAIS,grupos):
        x=np.sort(x)
        if len(x): axs[1].plot(x,np.arange(1,len(x)+1)/len(x),label=modal)
    axs[1].set_xscale('log')
    axs[1].set(xlabel='R$ de dez/2024 por m² (escala log)',ylabel='Fração acumulada',title='Distribuições acumuladas')
    axs[1].legend(fontsize=8)
    fmt=mticker.FuncFormatter(lambda v,_:f'{v:,.0f}'.replace(',','.'))
    axs[0].yaxis.set_major_locator(mticker.FixedLocator([3000,5000,10000,20000,30000]))
    axs[0].yaxis.set_major_formatter(fmt)
    axs[0].yaxis.set_minor_formatter(mticker.NullFormatter())
    axs[1].xaxis.set_major_locator(mticker.LogLocator(base=10,numticks=5))
    axs[1].xaxis.set_major_formatter(fmt)
    axs[1].xaxis.set_minor_formatter(mticker.NullFormatter())
    for ax in axs: ax.grid(alpha=.2)
    fig.tight_layout()
    return fig


def evolucao_anual(base, segundo_semestre=False):
    b=base.copy()
    if 'm2_real' not in b: b['m2_real']=corrigir_ipca(b)
    if segundo_semestre: b=b.loc[b.mes.ge(7)]
    return estatisticas(b,'ano')


def figura_anual(anual,semestre):
    fig,axs=plt.subplots(2,1,figsize=(9,6),sharex=True)
    anos=anual.index.to_numpy()
    axs[0].fill_between(anos,anual.q1.to_numpy(),anual.q3.to_numpy(),alpha=.18,label='Q1–Q3')
    axs[0].plot(anos,anual.mediana,marker='o',label='Mediana (meses disponíveis)')
    axs[0].plot(semestre.index,semestre.mediana,ls='--',label='Mediana (jul–dez)')
    axs[0].set(ylabel='R$ de dez/2024 por m²',title='Evolução real dos preços das transações')
    axs[1].plot(anos,anual.IIQ,marker='o',label='IIQ')
    axs[1].plot(anos,anual.desvio_padrao,marker='s',label='Desvio padrão')
    axs[1].plot(semestre.index,semestre.IIQ,ls='--',color='#1f77b4',label='IIQ (jul–dez)')
    axs[1].set(ylabel='R$ de dez/2024 por m²',xlabel='Ano',title='Dispersão ao longo dos anos')
    for ax in axs:
        ax.legend(fontsize=8);ax.grid(alpha=.2)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:f'{v:,.0f}'.replace(',','.')))
    fig.tight_layout()
    return fig


def sensibilidades(amostra):
    linhas=[]
    for limite in [300,500,800]:
        tab,_=comparar(amostra,limite=limite)
        tab['cenario']=f'{limite} m'; linhas.append(tab)
    antiga=amostra.loc[amostra.area.ge(25)&amostra.valor_m2.le(100_000)]
    tab,_=comparar(antiga);tab['cenario']='500 m + cortes antigos';linhas.append(tab)
    # Uma observação por coordenada/bairro/ano/tipologia, usando a mediana dos preços.
    dist=[c for c in amostra if c.startswith('dist_')]
    geo=amostra.groupby([*CHAVES,'id_grupo_geografico'],observed=True).agg(
        **{'m2_real':('m2_real','median'), **{c:(c,'first') for c in dist}}).reset_index()
    tab,_=comparar(geo);tab['cenario']='500 m + peso igual por local/ano/tipo';linhas.append(tab)
    return pd.concat(linhas,ignore_index=True)


def concentracao(amostra):
    linhas=[]
    for modal,col in MODAIS.items():
        b=amostra.loc[distancia_valida(amostra,col)&amostra[col].le(500)]
        cont=b.id_grupo_geografico.value_counts()
        linhas.append(dict(modalidade=modal,n=len(b),locais=len(cont),
            maior_local_pct=100*cont.iloc[0]/len(b) if len(b) else np.nan,
            dez_maiores_pct=100*cont.head(10).sum()/len(b) if len(b) else np.nan))
    return pd.DataFrame(linhas).set_index('modalidade')


def numero(v,casas=2):
    return f'{v:,.{casas}f}'.translate(str.maketrans({',':'.','.':','})) if pd.notna(v) else 'indefinido'


def conclusao(resumo,anual,grupos_disp,distribuicao,sensibilidade=None):
    r=resumo.set_index('modalidade')
    pico=anual.mediana.idxmax()
    partes=['## 7. Conclusão',
        'O mercado residencial do Rio apresenta forte assimetria de preços e heterogeneidade espacial. A mediana e os quartis descrevem melhor o imóvel típico do que a média isolada, e as comparações de transporte precisam considerar bairro, período, tipologia e cobertura.',
        f'No Metrô, a diferença agregada entre medianas perto e longe é de {numero(r.loc["Metrô","diferenca_geral_pct"])}%, enquanto a mediana das diferenças dentro dos grupos de bairro, ano e tipologia é de {numero(r.loc["Metrô","mediana_diferencas_grupos_pct"])}%. Esses números resumem conjuntos e estatísticas distintos; sua discrepância é compatível com diferenças de composição e não mede um efeito causal.',
        'Nas quatro modalidades, a análise de dispersão e das distribuições complementa os níveis de preço: a variabilidade não pode ser inferida apenas da mediana. A comparação entre modalidades usa uma amostra comum e explicita as sobreposições, sem tratar observações repetidas como amostras independentes.',
        f'Em valores corrigidos para dezembro de 2024, a mediana anual atinge seu maior nível em {int(pico)} e passa de R$ {numero(anual.loc[pico,"mediana"],0)} por m² nesse ano para R$ {numero(anual.loc[2024,"mediana"],0)} em 2024. Essa trajetória descreve transações de composição variável; não é um índice de preços de um imóvel de qualidade constante.',
        'O BRS foi incluído como proximidade ao corredor, uma aproximação distinta do acesso a uma estação. Registros sem data capazes de alterar a classificação são tratados como indeterminados. A geocodificação seletiva, o cadastro histórico incompleto, a concentração em poucos locais e a distância em linha reta limitam a generalização.',
        'As oito perguntas são respondidas de forma exploratória, com medidas de nível, dispersão, distribuição e evolução temporal. Os resultados sustentam uma associação descritiva entre localização, transporte e preços, mas não permitem atribuir valorização à implantação de uma modalidade nem recomendar investimentos específicos.']
    comparacoes=[]
    for modal in ['BRT','VLT','BRS (corredor)']:
        linha=r.loc[modal]
        comparacoes.append(f'{modal}: {numero(linha.diferenca_geral_pct)}% no agregado e {numero(linha.mediana_diferencas_grupos_pct)}% no resumo por grupo, com cobertura de {numero(linha.cobertura_amostra_pct)}% da amostra espacial de preços')
    partes.insert(3,'Para as demais modalidades, os resultados são '+ '; '.join(comparacoes)+'. Coberturas pequenas restringem a generalização, e o BRS deve ser interpretado como proximidade a corredor.')
    razoes='; '.join(f'{m}: {numero(linha.razao_IIQ_mediana)}' for m,linha in grupos_disp.iterrows())
    partes[4]='Na dispersão por bairro, ano e tipologia, as razões medianas de IIQ perto/longe são '+razoes+'. Valores acima de 1 indicam maior dispersão central perto; abaixo de 1, menor. Essa comparação também depende da cobertura e não decorre automaticamente do nível da mediana. A comparação das distribuições entre modalidades usa uma amostra comum e explicita as sobreposições, sem tratar observações repetidas como amostras independentes.'
    if sensibilidade is not None:
        instaveis=[];positivas=[]
        for modal,b in sensibilidade.groupby('modalidade',sort=False):
            v=b.mediana_diferencas_grupos_pct.dropna()
            if len(v) and v.min()<0<v.max():instaveis.append(modal)
            elif len(v) and v.min()>0:positivas.append(modal)
        partes.insert(6,'Na sensibilidade aos critérios de distância, filtro e peso por local, o resumo por grupos mantém sinal positivo em '+', '.join(positivas)+', enquanto há troca de sinal em '+', '.join(instaveis)+'. Isso impede uma conclusão geral de preços superiores perto de todas as modalidades. Os cenários também mudam unidades e cobertura, portanto essa variação não é um intervalo de confiança.')
    return '\n\n'.join(partes)
