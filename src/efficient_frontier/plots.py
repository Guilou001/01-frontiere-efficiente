"""Figures matplotlib (PNG + PDF vectoriel) avec le style ``assets/style.mplstyle``, heatmap seaborn, nuage Plotly.

Choix de couleurs : palette Okabe-Ito (cycle du style) pour les identités (actifs, stratégies) ; une seule
teinte de bleu, du clair au foncé, pour la grandeur continue (ratio de Sharpe du nuage) ; paire divergente
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
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .backtest import STRATEGY_LABELS  # noqa: E402
from .config import STYLE_FILE  # noqa: E402
from .frontier import Frontier  # noqa: E402
from .montecarlo import MonteCarloResult  # noqa: E402

STRATEGY_COLORS = {"max_sharpe": "#0072B2", "min_variance": "#E69F00", "inverse_vol": "#009E73", "equal_weight": "#D55E00"}
ESTIMATOR_STYLES = {"sample": "-", "ledoit_wolf": "--"}
ESTIMATOR_LABELS = {"sample": "échantillon", "ledoit_wolf": "Ledoit-Wolf"}


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
        fig.savefig(p)
    plt.close(fig)
    return paths


def _sharpe_cmap():
    base = plt.get_cmap("Blues")(np.linspace(0.35, 1.0, 256))
    return LinearSegmentedColormap.from_list("blues_truncated", base)


def plot_cloud(
    mc: MonteCarloResult,
    frontier: Frontier,
    special: dict[str, dict],
    asset_stats: pd.DataFrame,
    rf: float,
    stem: Path,
    title: str,
    unconstrained: pd.DataFrame | None = None,
) -> list[Path]:
    """Nuage Monte Carlo coloré par Sharpe, frontière QP, variance minimale, tangence, CML et actifs nommés."""
    fig, ax = plt.subplots(figsize=(7.4, 4.9))
    sc = ax.scatter(mc.vol * 100, mc.ret * 100, c=mc.sharpe, cmap=_sharpe_cmap(), s=2.5, alpha=0.55, linewidths=0, rasterized=True)
    cbar = fig.colorbar(sc, ax=ax, pad=0.015)
    cbar.set_label("ratio de Sharpe du portefeuille simulé")
    if unconstrained is not None:
        ax.plot(unconstrained["vol"] * 100, unconstrained["ret"] * 100, color="#7F7F7F", ls=":", lw=1.3,
                label="frontière sans contrainte de signe (forme fermée)")
    ax.plot(frontier.table["vol"] * 100, frontier.table["ret"] * 100, color="black", lw=1.9, label="frontière efficiente long-only (QP)")
    tan, mv = special["tangency"], special["min_variance"]
    x_max = max(frontier.table["vol"].max(), asset_stats["vol"].max()) * 1.12
    vols = np.linspace(0, x_max, 50)
    ax.plot(vols * 100, (rf + (tan["ret"] - rf) / tan["vol"] * vols) * 100, color="#D55E00", ls="--", lw=1.2,
            label="droite de marché des capitaux")
    ax.scatter([mv["vol"] * 100], [mv["ret"] * 100], marker="s", s=55, color="#E69F00", edgecolor="black", zorder=6,
               label=f"variance minimale (vol. {mv['vol'] * 100:.1f} %)")
    ax.scatter([tan["vol"] * 100], [tan["ret"] * 100], marker="*", s=170, color="#D55E00", edgecolor="black", zorder=7,
               label=f"tangence (Sharpe {tan['sharpe']:.2f})")
    ax.scatter([0], [rf * 100], marker="o", s=18, color="black", zorder=6)
    ax.annotate("taux sans risque", (0, rf * 100), xytext=(4, -9), textcoords="offset points", fontsize=7)
    ax.scatter(asset_stats["vol"] * 100, asset_stats["ret"] * 100, marker="D", s=20, color="black", zorder=6, label="actifs individuels")
    for k, (name, row) in enumerate(asset_stats.sort_values("vol").iterrows()):
        dy = 4 if k % 2 == 0 else -9
        ax.annotate(str(name), (row["vol"] * 100, row["ret"] * 100), xytext=(4, dy), textcoords="offset points", fontsize=7)
    ax.set_xlim(0, x_max * 100)
    ax.set_xlabel("volatilité annualisée (%)")
    ax.set_ylabel("rendement espéré annualisé (%)")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=7)
    return save(fig, stem)


def plot_transition_map(frontier: Frontier, stem: Path, title: str, markers: dict[str, float] | None = None) -> list[Path]:
    """Carte de transition : poids empilés le long de la frontière, en fonction de la volatilité cible."""
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = frontier.table["vol"].to_numpy() * 100
    w = frontier.weights.T * 100
    ax.stackplot(x, w, labels=frontier.assets, colors=asset_colors(len(frontier.assets)), alpha=0.9, linewidth=0.3, edgecolor="white")
    for name, v in (markers or {}).items():
        ax.axvline(v * 100, color="black", ls=":", lw=1)
        ax.text(v * 100, 97, name, ha="center", va="top", fontsize=7, bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0, 100)
    ax.set_xlabel("volatilité annualisée du portefeuille de la frontière (%)")
    ax.set_ylabel("poids (%)")
    ax.set_title(title)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7, ncol=1)
    return save(fig, stem)


def plot_corr_heatmap(corr: pd.DataFrame, stem: Path, title: str) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    sns.heatmap(corr, ax=ax, cmap="RdBu_r", vmin=-1, vmax=1, center=0, annot=True, fmt=".2f", annot_kws={"size": 6},
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.75, "label": "corrélation des rendements mensuels"})
    ax.set_title(title)
    ax.grid(False)
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
    return save(fig, stem)


def plot_oos_growth(returns_by_estimator: dict[str, pd.DataFrame], stem: Path, title: str, cost_bps: float) -> list[Path]:
    """Croissance cumulée hors échantillon (net de coûts) : couleur = stratégie, trait = estimateur."""
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    drawn_free = set()
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
            ax.annotate(f"{wealth.iloc[-1]:.2f}", (wealth.index[-1], wealth.iloc[-1]), xytext=(3, 0), textcoords="offset points",
                        fontsize=7, va="center", color=STRATEGY_COLORS[s])
    ax.set_ylabel(f"valeur de 1 unité investie (net de {cost_bps:g} pb par rotation)")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=7)
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
        x=mc.vol[idx] * 100, y=mc.ret[idx] * 100, mode="markers", name=f"portefeuilles simulés ({mc.sampling})",
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
                      template="simple_white", legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.7)"), width=950, height=600)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs="cdn")
    return path
