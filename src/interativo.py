"""Explorador interativo: o que muda quando alteramos a distância ou a medida de centro?

Usa a tabela de sensibilidade já calculada (500/800/1.000/1.500 m, média e mediana),
sem recalcular percursos nem fazer consultas externas. No notebook, controles ipywidgets.
Metrô, BRT e VLT cobrem 2011–2024; o BRS, apenas 2024.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
MODAIS = ["Metrô", "BRT", "VLT", "BRS"]
CORES = {"Metrô": "#2a78d6", "BRT": "#eb6834", "VLT": "#279b3b", "BRS": "#8856a7"}
LIMITES = [500, 800, 1000, 1500]
PERGUNTA = "O que muda quando alteramos a distância ou trocamos a mediana pela média?"
NOTA_PERIODO = "Metrô, BRT e VLT: 2011–2024. BRS: 2024."


def carregar(pasta=None):
    return pd.read_csv(Path(pasta or RAIZ / "resultados/historico") / "sensibilidade_limites_combinada.csv")


def _resumo(sens, limite, medida):
    g = sens.loc[sens.limite_m.eq(limite)].set_index("modalidade").reindex(MODAIS)
    p, l = g[f"{medida}_perto"], g[f"{medida}_longe"]
    dif = 100 * (p / l - 1)
    return g, p, l, dif


def _fmt(v, casas=0):
    return f"{v:,.{casas}f}".translate(str.maketrans({",": ".", ".": ","}))


def _frases(sens, limite, medida):
    g, p, l, dif = _resumo(sens, limite, medida)
    nome = "mediana" if medida == "mediana" else "média"
    frases = [f"Com corte de {_fmt(limite)} m e a {nome}, as diferenças perto/longe são:"]
    for m in MODAIS:
        sinal = "maior" if dif[m] >= 0 else "menor"
        frases.append(f"- {m}: preço {sinal} perto, {_fmt(dif[m], 1)}% "
                      f"({_fmt(p[m])} contra {_fmt(l[m])} R$/m²; "
                      f"{_fmt(g.loc[m, 'n_perto'])} perto e {_fmt(g.loc[m, 'n_longe'])} longe).")
    frases.append("Os valores são em reais de dezembro de 2024. Cada modalidade tem seu próprio "
                  "conjunto de transações classificáveis; a amostra também muda com o corte. "
                  + NOTA_PERIODO)
    return "\n".join(frases)


def _figura(sens, limite, medida):
    g, p, l, dif = _resumo(sens, limite, medida)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    yy = np.arange(len(MODAIS))[::-1]
    for y0, m in zip(yy, MODAIS):
        ax.barh(y0, dif[m], color=CORES[m], height=.55)
        ax.annotate(f"{dif[m]:+.1f}%".replace(".", ","),
                    (dif[m], y0), xytext=(6 if dif[m] >= 0 else -6, 0),
                    textcoords="offset points", va="center",
                    ha="left" if dif[m] >= 0 else "right", fontsize=9)
    ax.axvline(0, color="#555", lw=.9)
    ax.set_yticks(yy, MODAIS)
    nome = "Mediana" if medida == "mediana" else "Média"
    ax.set_xlabel("Diferença perto/longe (%)")
    ax.set_title(f"{nome} do preço por m² — corte de {_fmt(limite)} m")
    lo = min(dif.min(), 0) - 12
    hi = max(dif.max(), 0) + 16
    ax.set_xlim(lo, hi)
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    return fig


def widget_interativo(sens=None):
    """Controles no notebook: distância e medida de centro."""
    import ipywidgets as w
    from IPython.display import display, Markdown
    sens = carregar() if sens is None else sens
    display(Markdown(f"**{PERGUNTA}** {NOTA_PERIODO}"))
    dd = w.Dropdown(options=[(f"{_fmt(x)} m", x) for x in LIMITES], value=1000,
                    description="Distância:")
    tg = w.ToggleButtons(options=[("Mediana", "mediana"), ("Média", "media")],
                         value="mediana", description="Medida:")
    saida = w.Output()

    def render(*_):
        with saida:
            saida.clear_output(wait=True)
            display(Markdown(_frases(sens, dd.value, tg.value)))
            fig = _figura(sens, dd.value, tg.value)
            plt.show()
            plt.close(fig)

    dd.observe(render, "value")
    tg.observe(render, "value")
    render()
    display(w.VBox([w.HBox([dd, tg]), saida]))
