"""Comparações extras sugeridas após a apresentação intermediária."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from descritiva_proposta import CORES, LIMITE_PERTO, MODAIS, RAIZ, mascara_valida

FAIXAS = [0, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000]


def cobertura_mensal(base):
    return (pd.crosstab(base.ano, base.mes)
            .reindex(index=range(2011, 2025), columns=range(1, 13), fill_value=0)
            .fillna(0).astype(int))


def distancias_manhattan(locais, acessos=None):
    """Menor distância L1 aos mesmos pontos usados na rede pedestre."""
    if acessos is None:
        acessos = pd.read_csv(RAIZ / "resultados/proposta/acessos_referencia_2024.csv")
    locais = locais.drop_duplicates("id_grupo_geografico").set_index("id_grupo_geografico")
    projetar = Transformer.from_crs(4326, 31983, always_xy=True)
    xy = np.column_stack(projetar.transform(locais.lon_analise.to_numpy(),
                                           locais.lat_analise.to_numpy()))
    distancias = {}
    for modal, coluna in MODAIS.items():
        chave = coluna.split("_")[2]
        pontos = acessos.loc[acessos.modal.eq(chave) & acessos.acesso_conectado, ["x", "y"]]
        distancias[modal] = cKDTree(pontos.to_numpy()).query(xy, p=1)[0]
    return pd.DataFrame(distancias, index=locais.index)


def comparar_metricas(amostra, manhattan, limite):
    linhas = []
    for modal, coluna in MODAIS.items():
        m = amostra.id_grupo_geografico.map(manhattan[modal])
        valida = mascara_valida(amostra, coluna, limite) & m.notna()
        b = amostra.loc[valida]
        rede, grade = b[coluna].le(limite), m.loc[valida].le(limite)
        erro = (b[coluna] - m.loc[valida]).abs()
        precos_rede = b.groupby(rede).m2_real.median()
        precos_grade = b.groupby(grade).m2_real.median()
        linhas.append({
            "modalidade": modal, "n": len(b),
            "perto_a_pe": int(rede.sum()), "perto_manhattan": int(grade.sum()),
            "so_perto_a_pe": int((rede & ~grade).sum()),
            "so_perto_manhattan": int((~rede & grade).sum()),
            "mudam_pct": 100 * (rede != grade).mean(),
            "erro_absoluto_mediano_m": erro.median(),
            "dif_mediana_pe_pct": 100 * (precos_rede[True] / precos_rede[False] - 1),
            "dif_mediana_manhattan_pct": 100 * (precos_grade[True] / precos_grade[False] - 1),
        })
    return pd.DataFrame(linhas).set_index("modalidade")


def contrastes_por_grupo(amostra, limite, modais=None, mascara=None):
    """Mediana das diferenças entre imóveis do mesmo bairro e tipo."""
    modais = MODAIS if modais is None else modais
    mascara = mascara_valida if mascara is None else mascara
    linhas = []
    for modal, coluna in modais.items():
        b = amostra.loc[mascara(amostra, coluna, limite)].copy()
        b["perto"] = b[coluna].le(limite)
        g = (b.dropna(subset=["bairro", "ds_imovel_tipologia"])
             .groupby(["bairro", "ds_imovel_tipologia", "perto"])
             .agg(n=("m2_real", "size"), preco=("m2_real", "median"),
                  locais=("id_grupo_geografico", "nunique"))
             .unstack("perto").dropna())
        g = g.loc[g["n"].ge(10).all(axis=1) & g["locais"].ge(3).all(axis=1)]
        contraste = 100 * (g["preco"][True] / g["preco"][False] - 1)
        linhas.append({"modalidade": modal, "grupos": len(g), "transacoes": int(g["n"].sum().sum()),
                       "cobertura_pct": 100 * g["n"].sum().sum() / len(b),
                       "dif_mediana_pct": contraste.median(),
                       "q1_pct": contraste.quantile(.25), "q3_pct": contraste.quantile(.75)})
    return pd.DataFrame(linhas).set_index("modalidade")


def comparacoes_estratificadas(amostra, limite=LIMITE_PERTO, modais=None, mascara=None):
    """Três níveis de comparação perto/longe por modalidade, no mesmo recorte.

    1. Geral: todas as transações classificáveis da cidade.
    2. Restrito: apenas as vendas em grupos de bairro e tipo com pelo menos
       10 transações e 3 locais distintos de cada lado; medianas agregadas.
    3. Por grupo: mediana das diferenças calculadas dentro de cada grupo
       comparável (mesmo peso por grupo), com Q1 e Q3 entre grupos.
    """
    modais = MODAIS if modais is None else modais
    mascara = mascara_valida if mascara is None else mascara
    grupos = contrastes_por_grupo(amostra, limite, modais, mascara)
    linhas = []
    for modal, coluna in modais.items():
        b = amostra.loc[mascara(amostra, coluna, limite)].copy()
        b["perto"] = b[coluna].le(limite)
        g = (b.dropna(subset=["bairro", "ds_imovel_tipologia"])
             .groupby(["bairro", "ds_imovel_tipologia", "perto"])
             .agg(n=("m2_real", "size"), locais=("id_grupo_geografico", "nunique"))
             .unstack("perto").dropna())
        eleg = g.loc[g["n"].ge(10).all(axis=1) & g["locais"].ge(3).all(axis=1)]
        chaves = set(eleg.index)
        restrito = b.loc[b.set_index(["bairro", "ds_imovel_tipologia"]).index.isin(chaves)]
        p = restrito.loc[restrito.perto, "m2_real"]
        l = restrito.loc[~restrito.perto, "m2_real"]
        pg = b.loc[b.perto, "m2_real"]; lg = b.loc[~b.perto, "m2_real"]
        linhas.append({
            "modalidade": modal,
            "dif_geral_pct": 100 * (pg.median() / lg.median() - 1),
            "n_geral": len(b), "n_geral_perto": len(pg), "n_geral_longe": len(lg),
            "dif_restrito_pct": 100 * (p.median() / l.median() - 1),
            "n_restrito": len(restrito), "n_restrito_perto": len(p), "n_restrito_longe": len(l),
            "grupos": int(grupos.loc[modal, "grupos"]),
            "dif_grupos_mediana_pct": grupos.loc[modal, "dif_mediana_pct"],
            "grupos_q1_pct": grupos.loc[modal, "q1_pct"],
            "grupos_q3_pct": grupos.loc[modal, "q3_pct"],
            "cobertura_restrito_pct": 100 * len(restrito) / len(b),
        })
    return pd.DataFrame(linhas).set_index("modalidade")


def figura_tres_comparacoes(tab, periodo="2024", nota_extra=None):
    """As três comparações lado a lado, por modalidade."""
    fig, ax = plt.subplots(figsize=(9, 4.6))
    niveis = [
        ("dif_geral_pct", "Geral (cidade)", "o", "#2a78d6", .24),
        ("dif_restrito_pct", "Só grupos comparáveis", "s", "#eb6834", 0.0),
        ("dif_grupos_mediana_pct", "Mediana dos grupos", "D", "#279b3b", -.24),
    ]
    modais = list(MODAIS)
    yy = np.arange(len(modais))[::-1]
    for y0, modal in zip(yy, modais):
        r = tab.loc[modal]
        for col, rotulo, marca, cor, dy in niveis:
            v = r[col]
            ax.scatter(v, y0 + dy, marker=marca, s=70, color=cor, zorder=3,
                       label=rotulo if y0 == yy[0] else None)
            ax.annotate(f"{v:+.1f}%".replace(".", ","), (v, y0 + dy),
                        xytext=(7 if v >= 0 else -7, 0), textcoords="offset points",
                        va="center", ha="left" if v >= 0 else "right", fontsize=9, color=cor)
        ax.plot([r.grupos_q1_pct, r.grupos_q3_pct], [y0 - .24, y0 - .24],
                color="#279b3b", lw=3, alpha=.35, zorder=2)
    ax.axvline(0, color="#555", lw=.9)
    ax.set_yticks(yy, modais)
    ax.set_ylim(-.7, len(modais) - .3)
    xmin = min(tab[["dif_geral_pct", "dif_restrito_pct", "grupos_q1_pct"]].min().min(), -10)
    xmax = tab[["dif_geral_pct", "dif_restrito_pct", "grupos_q3_pct"]].max().max()
    ax.set_xlim(xmin - 12, xmax + 16)
    rotulo = f"Diferença entre medianas perto/longe (%) — {periodo}, até 1 km a pé" if periodo else "Diferença entre medianas perto/longe (%) — até 1 km a pé"
    ax.set_xlabel(rotulo)
    ax.set_title("Quanto do contraste geral permanece ao comparar bairro e tipo semelhantes?")
    ax.grid(axis="x", alpha=.2)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=9,
               bbox_to_anchor=(.5, .075))
    fig.text(.5, .045, "Haste verde: Q1–Q3 das diferenças entre grupos comparáveis.",
             ha="center", fontsize=8, color="#444")
    fig.text(.5, .015, "Níveis 2 e 3 usam os mesmos grupos (≥10 vendas e ≥3 locais distintos por lado).",
             ha="center", fontsize=8, color="#444")
    if nota_extra:
        fig.text(.5, .0, nota_extra, ha="center", fontsize=8, color="#444")
    fig.tight_layout(rect=(0, .14 if nota_extra else .12, 1, 1))
    return fig


def ajustar(x, y, forma):
    if forma == "Reta":
        inclinacao, intercepto = np.polyfit(x, y, 1)
        return lambda distancia: intercepto + inclinacao * distancia
    escala = np.median(y)
    # A escala interna evita misturar milhares de reais e expoentes no ajuste.
    a, b = least_squares(lambda p: np.exp(p[0] + p[1] * x) - y / escala,
                         x0=[0, 0], bounds=([-6, -2], [6, 2])).x
    return lambda distancia: escala * np.exp(a + b * distancia)


def perfil_precos(amostra, modais=None, amostras=None, periodos=None):
    """Curvas descritivas sobre as medianas por faixa, com o mesmo peso por faixa."""
    modais = MODAIS if modais is None else modais
    perfis, erros = [], []
    fig, eixos = plt.subplots(2, 2, figsize=(10, 6.6), sharex=True, sharey=True)
    for (modal, coluna), ax in zip(modais.items(), eixos.flat):
        base = amostras[modal] if amostras is not None else amostra
        limite_incerteza = coluna.removesuffix("_m") + "_acesso_ausente_reta_m"
        b = base.loc[base[coluna].notna()
                        & ~base[coluna].gt(base[limite_incerteza])].copy()
        b["faixa"] = pd.cut(b[coluna], FAIXAS, include_lowest=True)
        t = (b.groupby("faixa", observed=False)
             .agg(n=("m2_real", "size"), locais=("id_grupo_geografico", "nunique"),
                  preco=("m2_real", "median"), distancia=(coluna, "median"))
             .reset_index())
        t["usada"] = t.n.ge(30) & t.locais.ge(10)
        t["modalidade"] = modal
        perfis.append(t)
        x = t.loc[t.usada, "distancia"].to_numpy() / 1000
        y = t.loc[t.usada, "preco"].to_numpy()
        ax.scatter(x, y, label="Mediana por faixa", color=CORES[modal], zorder=3)
        linha = {"modalidade": modal, "faixas": len(x)}
        for forma, estilo in [("Reta", "--"), ("Exponencial", "-")]:
            rmse = np.nan
            if len(x) >= 5:
                predicoes = []
                for i in range(len(x)):
                    treino = np.arange(len(x)) != i
                    predicoes.append(ajustar(x[treino], y[treino], forma)(x[i]))
                rmse = np.sqrt(np.mean((y - predicoes) ** 2))
                grade = np.linspace(x.min(), x.max(), 100)
                ax.plot(grade, ajustar(x, y, forma)(grade), estilo, label=forma)
            linha[f"erro_{forma.lower()}"] = rmse
        erros.append(linha)
        titulo = modal if periodos is None else f"{modal} ({periodos[modal]})"
        ax.set_title(titulo)
        ax.grid(alpha=.2)
    handles, labels = eixos.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False)
    fig.supxlabel("Distância a pé (km)", y=.07)
    fig.supylabel("Preço mediano (R$ de dez/2024 por m²)")
    fig.tight_layout(rect=(.03, .10, 1, 1))
    return pd.concat(perfis, ignore_index=True), pd.DataFrame(erros).set_index("modalidade"), fig


def analisar(amostra, pasta=None, limite=LIMITE_PERTO):
    manhattan = distancias_manhattan(amostra)
    metricas = comparar_metricas(amostra, manhattan, limite)
    grupos = contrastes_por_grupo(amostra, limite)
    perfil, erros, figura = perfil_precos(amostra)
    pasta = Path(pasta or RAIZ / "resultados/proposta")
    pasta.mkdir(parents=True, exist_ok=True)
    metricas.to_csv(pasta / "comparacao_manhattan.csv")
    grupos.to_csv(pasta / "contrastes_bairro_tipo_2024.csv")
    perfil.to_csv(pasta / "precos_por_faixa_distancia.csv", index=False)
    erros.to_csv(pasta / "erros_reta_exponencial.csv")
    return metricas, grupos, perfil, erros, figura
