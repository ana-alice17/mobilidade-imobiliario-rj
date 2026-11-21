"""Mapa cadastral de transportes sobre o contexto geográfico do Rio."""
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely import from_wkb
from shapely.geometry import box

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "data/processed/mobilidade/base_cartografica_osm.gpkg"
FIGURA = RAIZ / "resultados/mapa_transportes.png"
CRS = 31983


def preparar_base(pbf):
    """Extrai o limite, as vias principais e a costa do PBF incluído."""
    import osmium

    fabrica = osmium.geom.WKBFactory()
    limite = []
    feicoes = []
    recorte = box(-43.83, -23.07, -43.09, -22.72)
    for item in osmium.FileProcessor(pbf).with_locations().with_areas():
        if item.is_area() and not item.from_way() and item.orig_id() == 2697338:
            limite.append(from_wkb(bytes.fromhex(fabrica.create_multipolygon(item))))
        if not item.is_way():
            continue
        via = item.tags.get("highway")
        classe = "costa" if item.tags.get("natural") == "coastline" else "via"
        if classe == "via" and via not in {"motorway", "trunk", "primary"}:
            continue
        try:
            linha = from_wkb(bytes.fromhex(fabrica.create_linestring(item)))
        except osmium.InvalidLocationError:
            # Algumas vias da borda do extrato referenciam nós externos.
            continue
        if linha.intersects(recorte):
            feicoes.append({"classe": classe, "geometry": linha.intersection(recorte)})
    if len(limite) != 1 or not {"via", "costa"} <= {x["classe"] for x in feicoes}:
        raise ValueError("Extrato incompleto para o mapa do município.")
    contorno = gpd.GeoSeries(limite, crs=4326).to_crs(CRS)
    contorno = contorno.make_valid().simplify(25)
    contorno.to_frame("geometry").to_file(BASE, layer="limite", index=False)
    linhas = gpd.GeoDataFrame(feicoes, crs=4326).to_crs(CRS)
    linhas.geometry = linhas.geometry.simplify(20)
    linhas.to_file(BASE, layer="contexto", index=False)


def desenhar_mapa():
    area = gpd.read_file(BASE, layer="limite")
    contexto = gpd.read_file(BASE, layer="contexto")
    fig, ax = plt.subplots(figsize=(11.6, 6.1))
    ax.set_facecolor("#f8fafb")
    area.plot(ax=ax, color="#edf1e6", edgecolor="#8c9888", linewidth=.8)
    contexto.loc[contexto.classe.eq("via")].plot(ax=ax, color="#ccd0ca", linewidth=.45)
    contexto.loc[contexto.classe.eq("costa")].plot(ax=ax, color="#86a9b7", linewidth=.7)

    camadas = [
        ("brs", "Corredores BRS", "#22784c", None),
        ("brt", "Paradas BRT", "#c07009", "o"),
        ("metro", "Estações de metrô", "#225bc1", "o"),
        ("vlt", "Paradas VLT", "#8e357c", "o"),
    ]
    legenda = []
    for arq, nome, cor, marcador in camadas:
        g = gpd.read_file(BASE.parent / f"{arq}_preparado.gpkg").to_crs(CRS)
        if marcador:
            g.plot(ax=ax, color=cor, markersize=17, edgecolor="white", linewidth=.35, zorder=4)
        else:
            g.plot(ax=ax, color=cor, linewidth=1.6, zorder=3)
        legenda.append(Line2D([], [], color=cor, marker=marcador,
                             linestyle="None" if marcador else "-", label=nome))
    legenda.append(Line2D([], [], color="#8c9888", label="Limite municipal"))
    ax.legend(handles=legenda, loc="upper left", frameon=True, framealpha=.97,
              facecolor="white", edgecolor="#d5dcdf", fontsize=10)

    rotulos = [
        ("Santa Cruz", -43.704, -22.908), ("Campo Grande", -43.566, -22.884),
        ("Barra da Tijuca", -43.373, -22.979), ("Centro", -43.163, -22.902),
        ("Baía de Guanabara", -43.151, -22.852), ("Oceano Atlântico", -43.310, -23.056),
    ]
    for nome, lon, lat in rotulos:
        ponto = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(CRS).iloc[0]
        ax.text(ponto.x, ponto.y, nome, ha="center", va="center", fontsize=9, color="#415c68",
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")], zorder=6)

    ax.set(xlim=(627500, 696200), ylim=(7446000, 7490500), aspect="equal", xlabel="", ylabel="")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#c9d2d6")
    ax.plot([631000, 636000], [7449100, 7449100], color="#35434a", lw=2)
    ax.text(633500, 7449800, "5 km", ha="center", va="bottom", fontsize=9, color="#35434a")
    ax.annotate("N", xy=(.965, .96), xytext=(.965, .87), xycoords="axes fraction",
                ha="center", fontsize=10, arrowprops={"arrowstyle": "-|>", "color": "#35434a"})
    fig.text(.13, .027, "Transporte: Data.Rio  ·  Base: © contribuidores do OpenStreetMap (out. 2026)",
             fontsize=9, color="#41515c")
    fig.subplots_adjust(left=.04, right=.99, bottom=.085, top=.985)
    return fig


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        preparar_base(sys.argv[1])
    FIGURA.parent.mkdir(exist_ok=True)
    desenhar_mapa().savefig(FIGURA, dpi=180, bbox_inches="tight", pad_inches=.15)
