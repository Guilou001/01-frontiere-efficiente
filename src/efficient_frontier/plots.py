"""Figures matplotlib (PNG + PDF vectoriel) avec le style ``assets/style.mplstyle``, heatmap seaborn, nuage Plotly.

Choix de couleurs : palette Okabe-Ito (cycle du style) pour les identités (actifs, stratégies) ; une seule
échelle viridis pour la grandeur continue (ratio de Sharpe du nuage) ; paire divergente
bleu/rouge à milieu neutre pour les corrélations.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from .backtest import STRATEGY_LABELS  # noqa: E402
from .config import STYLE_FILE  # noqa: E402
from .frontier import Frontier  # noqa: E402
from .montecarlo import MonteCarloResult  # noqa: E402

STRATEGY_COLORS = {"max_sharpe": "#0072B2", "min_variance": "#E69F00", "inverse_vol": "#009E73", "equal_weight": "#D55E00"}
ESTIMATOR_STYLES = {"sample": "-", "ledoit_wolf": "--"}
ESTIMATOR_LABELS = {"sample": "échantillon", "ledoit_wolf": "Ledoit-Wolf"}
SAMPLING_LABELS = {"dirichlet": "tirage de Dirichlet", "uniform": "tirage uniforme normalisé"}


def fr_num(x: float, dec: int = 2) -> str:
    """Nombre au format français : virgule décimale."""
    return f"{x:.{dec}f}".replace(".", ",")


#: formateur d'axe : virgule décimale sur les graduations numériques
FR_AXIS = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))


def fr_axes(*axes) -> None:
    """Applique la virgule décimale aux graduations des axes numériques donnés."""
    for ax in axes:
        ax.xaxis.set_major_formatter(FR_AXIS)
        ax.yaxis.set_major_formatter(FR_AXIS)


def use_style() -> None:
    if STYLE_FILE.exists():
        plt.style.use(str(STYLE_FILE))


def asset_colors(n: int) -> list[str]:
    cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    return [cycle[i % len(cycle)] for i in range(n)]


def save(fig, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = [stem.with_suffix(".png"), stem.with_suffix(".pdf")]
    for p in paths:
        fig.savefig(p, facecolor="white", edgecolor="white", transparent=False)
    plt.close(fig)
    return paths


def plot_cloud(
    mc: MonteCarloResult,
    frontier: Frontier,
    special: dict[str, dict],
    asset_stats: pd.DataFrame,
    rf: float,
    stem: Path,
    title: str,
    unconstrained: pd.DataFrame | None = None,
    finquant_check: pd.DataFrame | None = None,
) -> list[Path]:
    """Frontière sur fond blanc, contrôle FinQuant et trois portefeuilles expliqués.

    La droite de marché est limitée en longueur pour préserver la lisibilité du
    nuage. Son prolongement au-delà de la tangence suppose un emprunt au taux rf.
    """
    use_style()
    fig = plt.figure(figsize=(12, 7.4), facecolor="white")
    ax = fig.add_axes([0.075, 0.25, 0.60, 0.59], facecolor="white")
    side = fig.add_axes([0.73, 0.25, 0.25, 0.59], facecolor="white")
    side.set_axis_off()
    heading, _, subtitle = title.partition("\n")
    fig.text(0.075, 0.95, "Le meilleur compromis entre rendement et risque", fontsize=19,
             weight="bold", color="#152C40", va="top")
    fig.text(0.075, 0.90, heading, fontsize=9, color="#475569", va="top")
    sc = ax.scatter(mc.vol * 100, mc.ret * 100, c=mc.sharpe, cmap="viridis", s=3,
                    alpha=0.32, linewidths=0, rasterized=True, zorder=2)
    cax = fig.add_axes([0.075, 0.145, 0.28, 0.018])
    # Une échelle opaque conserve les couleurs réelles malgré la transparence du nuage.
    from matplotlib.cm import ScalarMappable
    cbar = fig.colorbar(ScalarMappable(norm=sc.norm, cmap=sc.cmap), cax=cax, orientation="horizontal")
    cbar.set_label("Ratio de Sharpe des portefeuilles simulés", fontsize=8)
    cbar.outline.set_visible(False)
    cbar.ax.xaxis.set_major_formatter(FR_AXIS)
    cbar.ax.tick_params(labelsize=8, length=0)
    if unconstrained is not None:
        ax.plot(unconstrained["vol"] * 100, unconstrained["ret"] * 100, color="#94A3B8", ls=":", lw=1.4,
                label="Vente à découvert permise", zorder=3)
    ax.plot(frontier.table["vol"] * 100, frontier.table["ret"] * 100, color="#152C40", lw=2.6,
            label="Frontière sans vente à découvert", zorder=4)
    if finquant_check is not None:
        fq = finquant_check.query("kind == 'frontier'")
        shown = fq.iloc[np.unique(np.linspace(0, len(fq) - 1, min(12, len(fq)), dtype=int))]
        ax.scatter(shown["vol"] * 100, shown["ret"] * 100, s=27, facecolors="white",
                   edgecolors="#007F73", linewidths=1.2, label="Recalcul FinQuant", zorder=5)
    tan = special["tangency"]
    has_tangency = tan["ret"] > rf and tan["vol"] > 0
    if has_tangency:
        vols = np.linspace(0, tan["vol"] * 1.22, 50)
        ax.plot(vols * 100, (rf + tan["sharpe"] * vols) * 100, color="#B85E0A", ls="--", lw=1.2,
                label="Combinaison avec le taux sans risque", zorder=3)
    points = [("min_variance", "Risque minimal", "s", "#0072B2"),
              ("tangency", "Meilleur ratio de Sharpe" if has_tangency else "Repli : risque minimal", "*", "#D55E00"),
              ("equal_weight", "Répartition égale (1/N)", "o", "#8064A2")]
    for k, (key, label, marker, color) in enumerate(points):
        stat = special[key]
        ax.scatter([stat["vol"] * 100], [stat["ret"] * 100], marker=marker,
                   s=155 if marker == "*" else 65, color=color, edgecolors="white", linewidths=1.0, zorder=7)
        y = 0.95 - k * 0.255
        side.text(0, y, label, color=color, fontsize=11, weight="bold", va="top")
        side.text(0, y - 0.07,
                  f"Rendement  {fr_num(stat['ret'] * 100, 1)} %\n"
                  f"Volatilité     {fr_num(stat['vol'] * 100, 1)} %\n"
                  f"Sharpe        {fr_num(stat['sharpe'])}",
                  fontsize=10, color="#334155", va="top", linespacing=1.6)
    side.text(0, 0.14, "Contrôle indépendant", fontsize=10, weight="bold", color="#007F73", va="top")
    if finquant_check is not None:
        gap = fq["vol_gap_bp"].abs().max()
        side.text(0, 0.08, f"{len(fq)} cibles recalculées avec FinQuant.\n"
                  f"Écart maximal : {fr_num(gap, 3)} pb\nde volatilité annualisée.",
                  fontsize=9, color="#475569", va="top", linespacing=1.5)
    ax.scatter(asset_stats["vol"] * 100, asset_stats["ret"] * 100, marker="D", s=24,
               color="#475569", edgecolors="white", linewidths=0.5, zorder=6)
    ax.scatter([0], [rf * 100], s=24, color="#475569", zorder=6)
    ax.annotate("Sans risque", (0, rf * 100), xytext=(6, -12), textcoords="offset points", fontsize=8)
    x_max = max(frontier.table["vol"].max(), asset_stats["vol"].max()) * 1.10
    ax.set_xlim(0, x_max * 100)
    ax.margins(y=0.15)
    ax.set_xlabel("Risque : volatilité annualisée (%)", labelpad=10)
    ax.set_ylabel("Rendement annuel estimé sur le passé (%)", labelpad=10)
    ax.spines[["left", "bottom"]].set_color("#CBD5E1")
    ax.grid(color="#E8EDF2", linewidth=0.6)
    ax.tick_params(length=0, pad=6)
    # Place les noms après fixation des axes ; évite les chevauchements, notamment XBB/XCB.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for k, (name, row) in enumerate(asset_stats.sort_values("vol").iterrows()):
        label = ax.annotate(str(name).removesuffix(".TO"), (row["vol"] * 100, row["ret"] * 100),
                            xytext=(5, 6), textcoords="offset points", fontsize=8, color="#334155",
                            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none", "pad": 0.5})
        offsets = [6, -11, 19, -24, 32, -37] if k % 2 == 0 else [-11, 6, -24, 19, -37, 32]
        for dy in offsets:
            label.set_position((5, dy))
            box = label.get_window_extent(renderer).expanded(1.15, 1.3)
            if not any(box.overlaps(other) for other in boxes):
                break
        boxes.append(box)
    fr_axes(ax)
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.39, 0.177),
               fontsize=7.5, ncol=1, handlelength=2.7)
    fig.text(0.075, 0.035, f"{subtitle} · Losanges : fonds individuels.\n"
             "Estimation historique, pas une prévision. Au-delà de l’étoile, la droite suppose un emprunt au taux sans risque.",
             fontsize=8, color="#64748B", va="bottom", linespacing=1.6)
    return save(fig, stem)


LEGEND_MIN_WEIGHT = 0.5  # % : seuil sous lequel un actif jamais retenu sort de la légende


def plot_transition_map(frontier: Frontier, stem: Path, title: str, markers: dict[str, float] | None = None) -> list[Path]:
    """Carte de transition : poids empilés le long de la frontière, en fonction de la volatilité cible.

    La légende ne liste que les actifs dont le poids maximal sur la frontière dépasse
    ``LEGEND_MIN_WEIGHT`` (en %) ; les aires des autres sont tracées mais invisibles (poids nuls).
    """
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = frontier.table["vol"].to_numpy() * 100
    w = frontier.weights.T * 100
    labels = [a if w[i].max() >= LEGEND_MIN_WEIGHT else "_nolegend_" for i, a in enumerate(frontier.assets)]
    ax.stackplot(x, w, labels=labels, colors=asset_colors(len(frontier.assets)), alpha=0.9, linewidth=0.3, edgecolor="white")
    for name, v in (markers or {}).items():
        ax.axvline(v * 100, color="black", ls=":", lw=1)
        ax.text(v * 100, 97, name, ha="center", va="top", fontsize=7, bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0, 100)
    ax.set_xlabel("volatilité annualisée du portefeuille de la frontière (%)")
    ax.set_ylabel("poids (%)")
    ax.set_title(title)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7, ncol=1,
              title=f"poids max. ≥ {fr_num(LEGEND_MIN_WEIGHT, 1)} %", title_fontsize=7)
    fr_axes(ax)
    return save(fig, stem)


def plot_corr_heatmap(corr: pd.DataFrame, stem: Path, title: str) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    annot = corr.map(lambda v: fr_num(v))
    sns.heatmap(corr, ax=ax, cmap="RdBu_r", vmin=-1, vmax=1, center=0, annot=annot, fmt="", annot_kws={"size": 6},
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.75, "label": "corrélation des rendements mensuels"})
    ax.set_title(title)
    ax.grid(False)
    ax.collections[0].colorbar.ax.yaxis.set_major_formatter(FR_AXIS)
    return save(fig, stem)


def plot_resampled_vs_analytical(frontier: Frontier, resampled: pd.DataFrame, stem: Path, title: str, n_boot: int) -> list[Path]:
    """Gauche : frontières analytique et rééchantillonnée ; droite : poids rééchantillonnés le long de la frontière."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0), gridspec_kw={"width_ratios": [1.0, 1.15]})
    ax1.plot(frontier.table["vol"] * 100, frontier.table["ret"] * 100, color="black", lw=1.9, label="analytique (QP sur les moments estimés)")
    ax1.plot(resampled["vol"] * 100, resampled["ret"] * 100, color="#D55E00", lw=1.9, marker="o", ms=3,
             label=f"rééchantillonnée (Michaud, {n_boot} bootstraps)")
    ax1.set_xlabel("volatilité annualisée (%)")
    ax1.set_ylabel("rendement espéré annualisé (%)")
    ax1.set_title("frontières évaluées sous les moments d'origine")
    ax1.legend(loc="lower right", fontsize=7)
    assets = frontier.assets
    w = resampled[["w_" + a for a in assets]].to_numpy().T * 100
    x = resampled["vol"].to_numpy() * 100
    ax2.stackplot(x, w, labels=assets, colors=asset_colors(len(assets)), alpha=0.9, linewidth=0.3, edgecolor="white")
    ax2.set_xlim(x.min(), x.max())
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("volatilité annualisée (%)")
    ax2.set_ylabel("poids moyens rééchantillonnés (%)")
    ax2.set_title("carte de transition rééchantillonnée")
    ax2.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7)
    fig.suptitle(title, fontsize=10)
    fr_axes(ax1, ax2)
    return save(fig, stem)


def plot_oos_growth(returns_by_estimator: dict[str, pd.DataFrame], stem: Path, title: str, cost_bps: float) -> list[Path]:
    """Croissance cumulée hors échantillon (net de coûts) : couleur = stratégie, trait = estimateur."""
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    drawn_free = set()
    ends: list[tuple[object, float, str]] = []
    for est, rets in returns_by_estimator.items():
        for s in rets.columns:
            if s in ("inverse_vol", "equal_weight"):
                if s in drawn_free:
                    continue
                drawn_free.add(s)
                label = STRATEGY_LABELS[s]
                ls = "-"
            else:
                label = f"{STRATEGY_LABELS[s]}, {ESTIMATOR_LABELS[est]}"
                ls = ESTIMATOR_STYLES[est]
            wealth = (1.0 + rets[s]).cumprod()
            ax.plot(wealth.index, wealth, color=STRATEGY_COLORS[s], ls=ls, lw=1.5, label=label)
            ends.append((wealth.index[-1], float(wealth.iloc[-1]), STRATEGY_COLORS[s]))
    # étiquettes finales décalées verticalement pour rester lisibles quand deux valeurs sont proches
    lo, hi = ax.get_ylim()
    gap = 0.035 * (hi - lo)
    y_prev = None
    for x_last, y, color in sorted(ends, key=lambda e: e[1]):
        y_lab = y if y_prev is None else max(y, y_prev + gap)
        y_prev = y_lab
        ax.annotate(fr_num(y), (x_last, y_lab), xytext=(3, 0), textcoords="offset points",
                    fontsize=7, va="center", color=color)
    ax.set_ylabel(f"valeur de 1 unité investie (net de {cost_bps:g} pb par rotation)")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=7)
    ax.yaxis.set_major_formatter(FR_AXIS)
    return save(fig, stem)


def plot_rolling_weights(weights: dict[str, pd.DataFrame], stem: Path, title: str) -> list[Path]:
    """Poids cibles glissants des quatre règles (aires empilées), une sous-figure par règle."""
    strategies = list(weights)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.0), sharex=True, sharey=True)
    assets = list(next(iter(weights.values())).columns)
    colors = asset_colors(len(assets))
    for ax, s in zip(axes.ravel(), strategies, strict=False):
        w = weights[s]
        ax.stackplot(w.index, w.to_numpy().T * 100, labels=assets, colors=colors, alpha=0.9, linewidth=0.2, edgecolor="white")
        ax.set_title(STRATEGY_LABELS[s], fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_xlim(w.index[0], w.index[-1])
        ax.yaxis.set_major_formatter(FR_AXIS)
    for ax in axes[:, 0]:
        ax.set_ylabel("poids (%)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(len(assets), 6), fontsize=7, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return save(fig, stem)


def plotly_cloud(
    mc: MonteCarloResult,
    frontier: Frontier,
    special: dict[str, dict],
    asset_stats: pd.DataFrame,
    rf: float,
    path: Path,
    title: str,
    max_points: int = 10_000,
    seed: int = 0,
) -> Path:
    """Nuage interactif (survol = poids du portefeuille), sous-échantillonné pour garder un HTML léger."""
    import plotly.graph_objects as go

    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(mc.n_sim, size=min(max_points, mc.n_sim), replace=False))
    texts = ["<br>".join(f"{a} : {w:.1%}" for a, w in zip(mc.assets, mc.weights[i], strict=True) if w >= 0.005) for i in idx]
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=mc.vol[idx] * 100, y=mc.ret[idx] * 100, mode="markers",
        name=f"portefeuilles simulés ({SAMPLING_LABELS.get(mc.sampling, mc.sampling)})",
        marker=dict(size=4, color=mc.sharpe[idx], colorscale="Blues", cmin=float(np.nanmin(mc.sharpe)), cmax=float(np.nanmax(mc.sharpe)),
                    colorbar=dict(title="Sharpe"), opacity=0.7),
        text=texts,
        hovertemplate="vol. %{x:.2f} %<br>rend. %{y:.2f} %<br>Sharpe %{marker.color:.2f}<br>%{text}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(x=frontier.table["vol"] * 100, y=frontier.table["ret"] * 100, mode="lines", name="frontière long-only",
                             line=dict(color="black", width=2), hovertemplate="vol. %{x:.2f} %<br>rend. %{y:.2f} %<extra>frontière</extra>"))
    tan, mv = special["tangency"], special["min_variance"]
    vols = np.linspace(0, frontier.table["vol"].max() * 1.05, 20)
    fig.add_trace(go.Scatter(x=vols * 100, y=(rf + (tan["ret"] - rf) / tan["vol"] * vols) * 100, mode="lines",
                             name="droite de marché des capitaux", line=dict(color="#D55E00", dash="dash", width=1.5)))
    fig.add_trace(go.Scatter(x=[mv["vol"] * 100], y=[mv["ret"] * 100], mode="markers", name="variance minimale",
                             marker=dict(symbol="square", size=11, color="#E69F00", line=dict(color="black", width=1))))
    fig.add_trace(go.Scatter(x=[tan["vol"] * 100], y=[tan["ret"] * 100], mode="markers", name=f"tangence (Sharpe {tan['sharpe']:.2f})",
                             marker=dict(symbol="star", size=15, color="#D55E00", line=dict(color="black", width=1))))
    fig.add_trace(go.Scatter(x=asset_stats["vol"] * 100, y=asset_stats["ret"] * 100, mode="markers+text", name="actifs",
                             text=list(asset_stats.index), textposition="top center", textfont=dict(size=9),
                             marker=dict(symbol="diamond", size=8, color="black")))
    fig.update_layout(title=title, xaxis_title="volatilité annualisée (%)", yaxis_title="rendement espéré annualisé (%)",
                      template="simple_white", paper_bgcolor="white", plot_bgcolor="white",
                      legend=dict(orientation="h", y=-0.22, x=0), margin=dict(b=145), width=1100, height=740)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs="cdn")
    return path
