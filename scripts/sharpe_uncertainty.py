"""Rejoue l'inférence depuis les rendements dérivés publiés, sans données externes.

Usage : uv run python scripts/sharpe_uncertainty.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from efficient_frontier import plots
from efficient_frontier.config import RESULTS
from efficient_frontier.inference import uncertainty_table


def plot_intervals(tables: dict[str, pd.DataFrame], stem: Path) -> None:
    plots.use_style()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4), sharex=True, sharey=True)
    colors = {"sample": "#0072B2", "ledoit_wolf": "#D55E00"}
    labels = {"us": "États-Unis", "canada": "Canada"}
    for ax, (universe, table) in zip(axes, tables.items(), strict=True):
        lengths = sorted(table.block_months.unique())
        for k, (estimator, color) in enumerate(colors.items()):
            subset = table[table.estimator == estimator].set_index("block_months").loc[lengths]
            y = np.arange(len(lengths)) + (k - 0.5) * 0.23
            # Segment et point séparés : un IC percentile peut ne pas contenir l'estimation.
            ax.hlines(y, subset.ci_low, subset.ci_high, color=color, linewidth=2.3)
            ax.scatter(subset.sharpe_difference, y, color=color, s=43,
                       label=plots.ESTIMATOR_LABELS[estimator], zorder=3)
        ax.axvline(0, color="#334155", linestyle="--", linewidth=1)
        ax.set_yticks(np.arange(len(lengths)), [f"Blocs de {n} mois" for n in lengths])
        ax.set_ylim(len(lengths) - 0.5, -0.5)
        row = table.iloc[0]
        ax.set_title(f"{labels[universe]}\n{row['start']} à {row['end']} ({row.n_months} mois)", fontsize=11, pad=12)
        ax.set_xlabel("Écart de Sharpe : optimisation moins répartition égale", fontsize=9)
        ax.xaxis.set_major_formatter(plots.FR_AXIS)
        ax.grid(axis="y", visible=False)
    confidence = tables["us"].confidence.iloc[0] * 100
    repetitions = int(tables["us"].n_boot.iloc[0])
    fig.suptitle(f"L'incertitude de l'écart de Sharpe : intervalles à {confidence:g} %", fontsize=16,
                 weight="bold", color="#152C40", y=0.98)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.55, 0.91),
               ncol=2, fontsize=10)
    fig.subplots_adjust(top=0.76, bottom=0.24, left=0.12, right=0.98, wspace=0.16)
    fig.text(0.12, 0.08,
             f"Points : écarts observés. Traits : intervalles percentiles, {repetitions:,} tirages appariés par longueur de bloc.\n".replace(",", " ")
             + f"Un intervalle qui traverse zéro ne permet pas de départager les règles au niveau nominal de {confidence:g} %.",
             fontsize=9, color="#475569", linespacing=1.6)
    plots.save(fig, stem)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--n-boot", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args(argv)
    tables = {}
    manifest = {"n_boot": args.n_boot, "seed": args.seed, "block_months": [3, 6, 12],
                "confidence": 0.95, "method": "paired_circular_percentile", "input_sha256": {}}
    for universe in ("us", "canada"):
        directory = args.results / "tables" / universe
        path = directory / "oos_inference_inputs.csv"
        inputs = pd.read_csv(path, index_col="date", parse_dates=True, float_precision="round_trip")
        tables[universe] = uncertainty_table(inputs, n_boot=args.n_boot, seed=args.seed)
        tables[universe].to_csv(directory / "oos_sharpe_uncertainty.csv", index=False, float_format="%.10f")
        manifest["input_sha256"][universe] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(universe)
        print(tables[universe][["estimator", "block_months", "sharpe_difference", "ci_low", "ci_high", "zero_in_interval"]].to_string(index=False))
    (args.results / "tables" / "sharpe_uncertainty_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    plot_intervals(tables, args.results / "figures" / "oos_sharpe_uncertainty")


if __name__ == "__main__":
    main()
