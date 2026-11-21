"""Comparações territoriais auditáveis: bairros e AP, com cobertura explícita.

As tabelas descrevem a amostra ITBI observada. Não representam todas as moradias,
nem estimam efeito causal do transporte. O parâmetro ``modais`` define a métrica;
colunas retas nunca recebem o rótulo de caminhada. Sem caminho/ano identificável,
a transação fica fora do denominador de distância daquela modalidade.
"""
from pathlib import Path
import json
import unicodedata
import numpy as np
import pandas as pd
from analise_mobilidade import corrigir_ipca

AREAS_PLANEJAMENTO = {'AP1 · Centro': ['SAUDE',
                  'GAMBOA',
                  'SANTO CRISTO',
                  'CAJU',
                  'CENTRO',
                  'CATUMBI',
                  'RIO COMPRIDO',
                  'CIDADE NOVA',
                  'ESTACIO',
                  'IMPERIAL DE SAO CRISTOVAO',
                  'MANGUEIRA',
                  'BENFICA',
                  'VASCO DA GAMA',
                  'PAQUETA',
                  'SANTA TERESA'],
 'AP2 · Zona Sul e Tijuca': ['FLAMENGO',
                             'GLORIA',
                             'LARANJEIRAS',
                             'CATETE',
                             'COSME VELHO',
                             'BOTAFOGO',
                             'HUMAITA',
                             'URCA',
                             'LEME',
                             'COPACABANA',
                             'IPANEMA',
                             'LEBLON',
                             'LAGOA',
                             'JARDIM BOTANICO',
                             'GAVEA',
                             'VIDIGAL',
                             'SAO CONRADO',
                             'ROCINHA',
                             'PRACA DA BANDEIRA',
                             'TIJUCA',
                             'ALTO DA BOA VISTA',
                             'MARACANA',
                             'VILA ISABEL',
                             'ANDARAI',
                             'GRAJAU'],
 'AP3 · Zona Norte': ['RAMOS',
                      'BONSUCESSO',
                      'OLARIA',
                      'MANGUINHOS',
                      'PENHA',
                      'PENHA CIRCULAR',
                      'BRAZ DE PINA',
                      'CORDOVIL',
                      'PARADA DE LUCAS',
                      'VIGARIO GERAL',
                      'JARDIM AMERICA',
                      'HIGIENOPOLIS',
                      'JACARE',
                      'MARIA DA GRACA',
                      'DEL CASTILHO',
                      'INHAUMA',
                      'ENGENHO DA RAINHA',
                      'TOMAS COELHO',
                      'JACAREZINHO',
                      'SAO FRANCISCO XAVIER',
                      'ROCHA',
                      'RIACHUELO',
                      'SAMPAIO',
                      'ENGENHO NOVO',
                      'LINS DE VASCONCELOS',
                      'MEIER',
                      'TODOS OS SANTOS',
                      'CACHAMBI',
                      'ENGENHO DE DENTRO',
                      'AGUA SANTA',
                      'ENCANTADO',
                      'PIEDADE',
                      'ABOLICAO',
                      'PILARES',
                      'VILA KOSMOS',
                      'VICENTE DE CARVALHO',
                      'VILA DA PENHA',
                      'VISTA ALEGRE',
                      'IRAJA',
                      'COLEGIO',
                      'CAMPINHO',
                      'QUINTINO BOCAIUVA',
                      'CAVALCANTI',
                      'ENGENHEIRO LEAL',
                      'CASCADURA',
                      'MADUREIRA',
                      'VAZ LOBO',
                      'TURIACU',
                      'ROCHA MIRANDA',
                      'HONORIO GURGEL',
                      'OSWALDO CRUZ',
                      'BENTO RIBEIRO',
                      'MARECHAL HERMES',
                      'GUADALUPE',
                      'ANCHIETA',
                      'PARQUE ANCHIETA',
                      'RICARDO DE ALBUQUERQUE',
                      'COELHO NETO',
                      'ACARI',
                      'BARROS FILHO',
                      'COSTA BARROS',
                      'PAVUNA',
                      'PARQUE COLUMBIA',
                      'RIBEIRA',
                      'ZUMBI',
                      'CACUIA',
                      'PITANGUEIRAS',
                      'PRAIA DA BANDEIRA',
                      'COCOTA',
                      'BANCARIOS',
                      'FREGUESIA ILHA',
                      'JARDIM GUANABARA',
                      'JARDIM CARIOCA',
                      'TAUA',
                      'MONERO',
                      'PORTUGUESA',
                      'GALEAO',
                      'CIDADE UNIVERSITARIA',
                      'COMPLEXO DO ALEMAO',
                      'MARE'],
 'AP4 · Barra e Jacarepaguá': ['JACAREPAGUA',
                               'ANIL',
                               'GARDENIA AZUL',
                               'CIDADE DE DEUS',
                               'CURICICA',
                               'FREGUESIA JACAREPAGUA',
                               'PECHINCHA',
                               'TAQUARA',
                               'TANQUE',
                               'PRACA SECA',
                               'VILA VALQUEIRE',
                               'JOA',
                               'ITANHANGA',
                               'BARRA DA TIJUCA',
                               'CAMORIM',
                               'VARGEM PEQUENA',
                               'VARGEM GRANDE',
                               'RECREIO DOS BANDEIRANTES',
                               'GRUMARI'],
 'AP5 · Zona Oeste': ['DEODORO',
                      'VILA MILITAR',
                      'CAMPO DOS AFONSOS',
                      'JARDIM SULACAP',
                      'MAGALHAES BASTOS',
                      'REALENGO',
                      'PADRE MIGUEL',
                      'BANGU',
                      'SENADOR CAMARA',
                      'GERICINO',
                      'SANTISSIMO',
                      'CAMPO GRANDE',
                      'SENADOR VASCONCELOS',
                      'INHOAIBA',
                      'COSMOS',
                      'PACIENCIA',
                      'SANTA CRUZ',
                      'SEPETIBA',
                      'GUARATIBA',
                      'BARRA DE GUARATIBA',
                      'PEDRA DE GUARATIBA']}

BAIRRO_AP = {b: ap for ap, bairros in AREAS_PLANEJAMENTO.items() for b in bairros}
MODAIS_RETA = {"Metrô": "dist_metro_m", "BRT": "dist_brt_m", "VLT": "dist_vlt_m",
               "BRS (corredor)": "dist_brs_m"}
MODAIS_CAMINHADA = {"Metrô": "dist_walk_metro_m", "BRT": "dist_walk_brt_m",
                   "VLT": "dist_walk_vlt_m"}
CHAVE_DUPLICATA = ["ano", "mes", "regiao_fiscal", "CD_BAIRRO", "cl", "trecho",
                    "cod_tipologia", "id_utilizacao", "numero", "COMPLEMENTO",
                    "nm_bairro_norm", "logradouro", "ds_imovel_tipologia", "DESCRICAO",
                    "parte_transferida", "valor_transacoes", "area", "valor_m2"]


def normalizar_bairro(valor):
    if pd.isna(valor): return pd.NA
    texto = unicodedata.normalize("NFKD", str(valor).upper())
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).split())


def preparar_territorios(base):
    b = base.copy()
    b["bairro"] = b.nm_bairro_norm.map(normalizar_bairro)
    b["ap"] = b.bairro.map(BAIRRO_AP)
    if "m2_real" not in b:
        b["m2_real"] = corrigir_ipca(b)
    b["faixa_area"] = pd.cut(b.area, [0, 50, 80, 120, np.inf],
        labels=["até 50", "50 a 80", "80 a 120", "mais de 120"], include_lowest=True)
    b["semestre"] = np.where(b.mes.le(6), 1, 2)
    return b


def filtro_precos(base):
    flag = base.valor_m2_suspeito.astype(str).str.strip().str.lower()
    if not flag.isin(["true", "false"]).all():
        raise ValueError("Sinalização de preços ausente ou inválida.")
    return np.isfinite(base.valor_m2) & base.valor_m2.gt(0) & flag.eq("false")


def mascara_distancia(base, col, limite):
    """Ausência de caminho nunca significa 'longe'. Incerteza temporal preservada."""
    valida = np.isfinite(base[col]) & base[col].ge(0)
    prefixo = col.removesuffix("_m")
    for incerta in [prefixo+"_sem_ano_m", prefixo+"_abertura_no_ano_m",
                    prefixo+"_acesso_ausente_reta_m", prefixo+"_abertura_no_ano_reta_m",
                    prefixo+"_sem_ano_reta_m"]:
        if incerta in base:
            valida &= ~(base[col].gt(limite) & base[incerta].le(limite))
    # O contrato do roteador exclui conexões rejeitadas da coluna numérica.
    return valida


def mascara_distancia_continua(base, col):
    """Uma rota conhecida só identifica o mínimo se nenhuma candidata puder encurtá-la.

    Distância até entrada confirmada é limite superior da distância mínima quando
    existe uma estação omitida/temporalmente incerta possivelmente mais próxima.
    Quantis contínuos excluem esses casos; os limiares usam a guarda específica.
    """
    valida = np.isfinite(base[col]) & base[col].ge(0)
    prefixo = col.removesuffix("_m")
    for sufixo in ["_sem_ano_m", "_abertura_no_ano_m", "_acesso_ausente_reta_m",
                   "_abertura_no_ano_reta_m", "_sem_ano_reta_m"]:
        candidata = prefixo+sufixo
        if candidata in base:
            valida &= ~base[col].gt(base[candidata])
    return valida


def resumo_distancias(amostra, modais, limites=(500, 800, 1000, 1500)):
    linhas = []
    for nivel in ["bairro", "ap"]:
        totais = amostra.groupby(nivel, observed=True).size()
        for modal, col in modais.items():
            for territorio, grupo in amostra.groupby(nivel, observed=True):
                numerica = grupo.loc[np.isfinite(grupo[col]) & grupo[col].ge(0), col]
                d = grupo.loc[mascara_distancia_continua(grupo, col), col]
                n_locais = grupo.loc[d.index, 'id_grupo_geografico'].nunique()
                suporte = len(d) >= 10 and n_locais >= 3
                linha = dict(nivel=nivel, territorio=territorio, modalidade=modal,
                    n_amostra=len(grupo), n_distancia=len(numerica),
                    n_distancia_continua_identificada=len(d),
                    locais_distancia_continua=n_locais, suporte_continuo_suficiente=suporte,
                    cobertura_distancia_pct=100*len(numerica)/len(grupo),
                    cobertura_continua_identificada_pct=100*len(d)/len(grupo),
                    mediana_rota_confirmada_m=numerica.median(),
                    p10_m=d.quantile(.1), p25_m=d.quantile(.25),
                    mediana_m=d.median(), media_m=d.mean(), p75_m=d.quantile(.75),
                    p90_m=d.quantile(.9), locais=grupo.id_grupo_geografico.nunique())
                if not suporte:
                    for campo in ['p10_m','p25_m','mediana_m','media_m','p75_m','p90_m']:
                        linha[campo] = np.nan
                for limite in limites:
                    v = mascara_distancia(grupo, col, limite)
                    linha[f"n_classificaveis_{limite}m"] = int(v.sum())
                    linha[f"n_perto_{limite}m"] = int((v & grupo[col].le(limite)).sum())
                    linha[f"perto_{limite}m_pct"] = (100*grupo.loc[v, col].le(limite).mean())
                linhas.append(linha)
    return pd.DataFrame(linhas)


def comparar_territorios(amostra, modais, limite=800, minimo=10, min_locais=3,
                         ajustar_area=False):
    """Duas unidades: agregado do território e mediana dos contrastes por estrato.

    O resumo ajustado exige >= ``minimo`` transações E >= ``min_locais`` locais
    em cada lado de bairro×ano×tipologia. No cenário de área, adiciona faixa de
    área e semestre. Cada estrato recebe peso igual; não se interpreta isso como
    coeficiente causal, teste de hipótese ou valorização ao longo do tempo.
    """
    detalhes, resumos = [], []
    chaves = ["bairro", "ano", "ds_imovel_tipologia"]
    if ajustar_area: chaves += ["faixa_area", "semestre"]
    for modal, col in modais.items():
        v = mascara_distancia(amostra, col, limite)
        b = amostra.loc[v].copy()
        b["perto"] = b[col].le(limite)
        agrupado = b.groupby(chaves+["perto"], observed=True)
        tab = agrupado.agg(n=("m2_real", "size"),
            locais=("id_grupo_geografico", "nunique"), mediana=("m2_real", "median"))
        quantis = agrupado.m2_real.quantile([.25, .75]).unstack(-1)
        tab["q1"] = quantis.reindex(columns=[.25, .75])[.25]
        tab["q3"] = quantis.reindex(columns=[.25, .75])[.75]
        g = tab.unstack("perto").reindex(columns=pd.MultiIndex.from_product(
            [["n", "locais", "mediana", "q1", "q3"], [False, True]]))
        # Reindex mantém os dois lados inclusive quando todos os registros estão
        # próximos ou todos distantes; nenhum grupo unilateral vira comparação.
        elegivel = ((g["n"].fillna(0).ge(minimo)).all(axis=1)
                    & (g["locais"].fillna(0).ge(min_locais)).all(axis=1))
        g = g.loc[elegivel].copy()
        d = pd.DataFrame(index=g.index)
        for lado, flag in [("longe", False), ("perto", True)]:
            for campo in ["n", "locais", "mediana"]:
                d[f"{campo}_{lado}"] = g[(campo, flag)]
            d[f"iiq_{lado}"] = g[("q3", flag)] - g[("q1", flag)]
        d["diferenca_pct"] = 100*(d.mediana_perto/d.mediana_longe-1)
        d["razao_iiq"] = d.iiq_perto/d.iiq_longe.where(d.iiq_longe.gt(0))
        d = d.reset_index()
        d["ap"] = d.bairro.map(BAIRRO_AP)
        d["modalidade"] = modal
        d["limite_m"] = limite
        d["cenario"] = "bairro_ano_tipo_area_semestre" if ajustar_area else "bairro_ano_tipo"
        detalhes.append(d)
        for nivel in ["bairro", "ap"]:
            for territorio, universo in amostra.groupby(nivel, observed=True):
                local = b.loc[b[nivel].eq(territorio)]
                perto = local.loc[local.perto]
                longe = local.loc[~local.perto]
                est = d.loc[d[nivel].eq(territorio)]
                n_est = int(est.n_perto.sum()+est.n_longe.sum())
                valido_agregado = len(perto)>=minimo and len(longe)>=minimo
                resumos.append(dict(nivel=nivel, territorio=territorio, modalidade=modal,
                    limite_m=limite, cenario=d.cenario.iloc[0] if len(d) else (
                        "bairro_ano_tipo_area_semestre" if ajustar_area else "bairro_ano_tipo"),
                    n_amostra=len(universo), n_distancia=len(local),
                    n_perto=len(perto), n_longe=len(longe),
                    locais_perto=perto.id_grupo_geografico.nunique(),
                    locais_longe=longe.id_grupo_geografico.nunique(),
                    mediana_perto=perto.m2_real.median(), mediana_longe=longe.m2_real.median(),
                    media_perto=perto.m2_real.mean(), media_longe=longe.m2_real.mean(),
                    iiq_perto=perto.m2_real.quantile(.75)-perto.m2_real.quantile(.25),
                    iiq_longe=longe.m2_real.quantile(.75)-longe.m2_real.quantile(.25),
                    comparavel_agregado=valido_agregado,
                    diferenca_agregada_pct=(100*(perto.m2_real.median()/longe.m2_real.median()-1)
                        if valido_agregado else np.nan),
                    estratos_comparaveis=len(est), n_em_estratos=n_est,
                    cobertura_estratos_pct=100*n_est/len(universo),
                    mediana_diferencas_estratos_pct=est.diferenca_pct.median(),
                    q1_diferencas_estratos_pct=est.diferenca_pct.quantile(.25),
                    q3_diferencas_estratos_pct=est.diferenca_pct.quantile(.75),
                    mediana_razao_iiq=est.razao_iiq.median(),
                    estratos_iiq_definido=int(est.razao_iiq.notna().sum())))
    return pd.DataFrame(resumos), pd.concat(detalhes, ignore_index=True)


def cobertura_geocodificacao(universo, amostra):
    """Compara denominadores: universo com preços válidos vs amostra espacial."""
    linhas = []
    for nivel in ["bairro", "ap"]:
        n_espacial = amostra.groupby(nivel, observed=True).size()
        for territorio, b in universo.groupby(nivel, observed=True):
            selecao = amostra.loc[amostra[nivel].eq(territorio)]
            n = int(n_espacial.get(territorio, 0))
            linhas.append(dict(nivel=nivel, territorio=territorio, n_universo=len(b),
                n_espacial=n, cobertura_espacial_pct=100*n/len(b),
                mediana_universo=b.m2_real.median(), mediana_espacial=selecao.m2_real.median(),
                diferenca_mediana_selecao_pct=100*(selecao.m2_real.median()/b.m2_real.median()-1)))
    return pd.DataFrame(linhas)


def auditoria_duplicatas(base):
    chaves = [c for c in CHAVE_DUPLICATA if c in base]
    dup = base.duplicated(chaves, keep="first")
    return {"chave_candidata": chaves, "registros": len(base),
            "copias_candidatas": int(dup.sum()), "pct_copias": 100*dup.mean(),
            "interpretacao": "Coincidência dos campos disponíveis não prova duplicação; "
            "não excluir automaticamente sem identificador original de negócio ou matrícula."}


def executar(base, universo, pasta, modais=None, limites=(500, 800, 1000, 1500),
             metrica="caminhada", principal=800):
    pasta = Path(pasta); pasta.mkdir(parents=True, exist_ok=True)
    modais = modais or MODAIS_CAMINHADA
    faltam = set(modais.values()) - set(base)
    if faltam: raise ValueError(f"Colunas ausentes para {metrica}: {sorted(faltam)}")
    amostra = preparar_territorios(base.loc[filtro_precos(base)].copy())
    completo = preparar_territorios(universo.loc[filtro_precos(universo)].copy())
    dist = resumo_distancias(amostra, modais, limites)
    dist["metrica"] = metrica
    dist.to_csv(pasta/"distancias_bairro_ap.csv", index=False)
    distancia_anual = []
    for ano, grupo in amostra.groupby("ano", observed=True):
        t = resumo_distancias(grupo, modais, limites)
        t["ano"] = int(ano); t["metrica"] = metrica
        distancia_anual.append(t)
    pd.concat(distancia_anual, ignore_index=True).to_csv(
        pasta/"distancias_bairro_ap_ano.csv", index=False)
    cobertura = cobertura_geocodificacao(completo, amostra)
    cobertura.to_csv(pasta/"cobertura_geocodificacao_bairro_ap.csv", index=False)
    resumos = []; detalhes = []
    for limite in limites:
        r,d = comparar_territorios(amostra, modais, limite=limite)
        resumos.append(r); detalhes.append(d)
    r,d = comparar_territorios(amostra, modais, limite=principal, ajustar_area=True)
    resumos.append(r); detalhes.append(d)
    # Cópias só saem de um cenário de sensibilidade; a base analítica é preservada.
    dedup = amostra.drop_duplicates([c for c in CHAVE_DUPLICATA if c in amostra])
    r,d = comparar_territorios(dedup, modais, limite=principal)
    r["cenario"] = d["cenario"] = "sem_copias_candidatas"
    resumos.append(r); detalhes.append(d)
    resumo = pd.concat(resumos, ignore_index=True)
    detalhe = pd.concat(detalhes, ignore_index=True)
    resumo["metrica"] = detalhe["metrica"] = metrica
    resumo.to_csv(pasta/"precos_dispersao_bairro_ap.csv", index=False)
    detalhe.to_csv(pasta/"contrastes_bairro_ano_tipo.csv", index=False)
    manifesto = dict(metrica=metrica, modais=modais, limites=list(limites), principal=principal,
        minimo_transacoes_por_lado=10, minimo_locais_por_lado=3,
        estratos="bairro × ano × tipologia; robustez adiciona faixa de área e semestre",
        pesos="mediana dos contrastes; cada estrato recebe peso igual",
        n_precos_universo=len(completo), n_precos_espacial=len(amostra),
        bairros_sem_ap=sorted(amostra.loc[amostra.ap.isna(), "bairro"].dropna().unique().tolist()),
        duplicatas=auditoria_duplicatas(amostra),
        quantis_distancia="Somente mínimos identificáveis; excluem candidatas incertas com lower bound menor que a rota conhecida.",
        inferencia="Descritiva. Faixas e contrastes não são testes, efeito causal nem índice hedônico.")
    (pasta/"manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2),encoding="utf-8")
    return dist, resumo, detalhe, cobertura, manifesto


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="data/processed/itbi_com_distancias.csv.gz")
    parser.add_argument("--universo", default="data/processed/itbi_residencial_2011_2024_geocodificado_completo.csv.gz")
    parser.add_argument("--pasta", default="resultados/territorial")
    parser.add_argument("--reta-diagnostico", action="store_true")
    a = parser.parse_args()
    modais = MODAIS_RETA if a.reta_diagnostico else MODAIS_CAMINHADA
    metrica = "reta_diagnostico_sem_percurso" if a.reta_diagnostico else "caminhada"
    print(executar(pd.read_csv(a.base,low_memory=False), pd.read_csv(a.universo,low_memory=False),
        a.pasta, modais=modais, metrica=metrica)[-1])
