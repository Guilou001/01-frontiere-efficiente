"""Barres groupées du ratio de Sharpe hors échantillon net par règle, É.-U. et Canada côte à côte.

Lit ``results/tables/us/oos_metrics.csv`` et ``results/tables/canada/oos_metrics.csv`` (règles
optimisées sous moments échantillon), écrit ``results/figures/oos_sharpe_bars.png`` et ``.pdf``.
Usage : ``uv run python scripts/plot_oos_sharpe.py``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from efficient_frontier import plots
from efficient_frontier.backtest import STRATEGIES, STRATEGY_LABELS
from efficient_frontier.config import RESULTS

# paire Okabe-Ito du style du dépôt, validée pour le daltonisme (ΔE CVD 21,9, contraste >= 3:1)
UNIVERSE_COLORS = {"us": "#0072B2", "canada": "#D55E00"}
UNIVERSE_LABELS = {"us": "É.-U.", "canada": "Canada"}


def load_sharpe(universe: str) -> tuple[pd.Series, str]:
    """Sharpe net par règle (moments échantillon pour les règles optimisées) et période du backtest."""
    df = pd.read_csv(RESULTS / "tables" / universe / "oos_metrics.csv")
    df = df[df["estimator"].isin(["sample", "aucun"])].set_index("strategy")
    return df["sharpe"].reindex(list(STRATEGIES)), str(df["period"].iloc[0])


def main() -> None:
    plots.use_style()
    data = {u: load_sharpe(u) for u in UNIVERSE_COLORS}
    x = np.arange(len(STRATEGIES))
    width = 0.38
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for k, (u, (sharpe, period)) in enumerate(data.items()):
        values = sharpe.to_numpy()
        bars = ax.bar(x + (k - 0.5) * width, values, width=width * 0.94, color=UNIVERSE_COLORS[u],
                      label=f"{UNIVERSE_LABELS[u]}, {period}", edgecolor="white", linewidth=0.5)
        for rect, v in zip(bars, values, strict=True):
            ax.annotate(plots.fr_num(v), (rect.get_x() + rect.get_width() / 2, v), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8)
    ax.set_xticks(x, [STRATEGY_LABELS[s].replace(" (", "\n(") for s in STRATEGIES])
    ax.set_ylabel("ratio de Sharpe hors échantillon (net de 10 pb par rotation)")
    ax.set_ylim(0, max(v for s, _ in data.values() for v in s) * 1.18)
    ax.set_title("Le Sharpe maximal bat 1/N aux États-Unis et perd au Canada\n"
                 "fenêtre 60 mois, moments échantillon pour les règles optimisées")
    ax.legend(loc="upper right", fontsize=8)
    ax.yaxis.set_major_formatter(plots.FR_AXIS)
    for p in plots.save(fig, RESULTS / "figures" / "oos_sharpe_bars"):
        print(p)


if __name__ == "__main__":
    main()
