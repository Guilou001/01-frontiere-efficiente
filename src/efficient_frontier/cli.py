"""Ligne de commande : ``efficient-frontier run`` (données réelles en cache) et ``efficient-frontier demo`` (synthétique)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import DATA_RAW, RESULTS, UNIVERSES
from .data import load_universe, synthetic_universe
from .estimation import ESTIMATORS
from .pipeline import run_pipeline


def _common(p: argparse.ArgumentParser, n_sim: int, n_boot: int) -> None:
    p.add_argument("--n-sim", type=int, default=n_sim, help="nombre de portefeuilles Monte Carlo par tirage")
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--estimator", choices=ESTIMATORS, default="sample")
    p.add_argument("--n-points", type=int, default=60, help="points de la frontière")
    p.add_argument("--n-boot", type=int, default=n_boot, help="bootstraps de la frontière rééchantillonnée")
    p.add_argument("--window", type=int, default=60, help="fenêtre d'estimation du backtest (mois)")
    p.add_argument("--cost-bps", type=float, default=10.0, help="coût aller simple en points de base")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="efficient-frontier", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="pipeline complet sur un univers réel (prix en cache dans data/raw)")
    run.add_argument("--universe", choices=sorted(UNIVERSES), required=True)
    run.add_argument("--data-dir", type=Path, default=DATA_RAW)
    run.add_argument("--out", type=Path, default=RESULTS, help="dossier results/ (tables/<univers>, figures/<univers>)")
    _common(run, n_sim=50_000, n_boot=200)

    demo = sub.add_parser("demo", help="pipeline sur un univers synthétique, sans réseau (CI)")
    demo.add_argument("--out", type=Path, default=RESULTS / "demo")
    demo.add_argument("--n-assets", type=int, default=6)
    demo.add_argument("--n-months", type=int, default=240)
    _common(demo, n_sim=20_000, n_boot=50)
    return parser


def _print_summary(summary: dict, elapsed: float) -> None:
    tan = summary["special_portfolios"]["tangency"]
    mv = summary["special_portfolios"]["min_variance"]
    print(f"{summary['label']} : {summary['n_assets']} actifs, {summary['period']} ({summary['n_months']} mois), "
          f"estimateur {summary['estimator']}" + (f", delta Ledoit-Wolf {summary['shrinkage']:.3f}" if summary["shrinkage"] is not None else ""))
    print(f"  tangence : rendement {tan['ret']:.2%}, vol. {tan['vol']:.2%}, Sharpe {tan['sharpe']:.3f}")
    print(f"  variance minimale : rendement {mv['ret']:.2%}, vol. {mv['vol']:.2%}, Sharpe {mv['sharpe']:.3f}")
    for rec in summary["montecarlo"]:
        print(f"  Monte Carlo {rec['sampling']} : meilleur Sharpe {rec['mc_best_sharpe']:.3f} (tangence {rec['tangency_sharpe']:.3f}), "
              f"vol. min {rec['mc_min_vol']:.2%} (var. min {rec['min_var_vol']:.2%})")
    print("  Sharpe hors échantillon : " + ", ".join(f"{k} {v:.2f}" for k, v in summary["oos_sharpe"].items()))
    print(f"  durée {elapsed:.1f} s")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    t0 = time.time()
    if args.command == "run":
        returns, rf, universe = load_universe(args.universe, args.data_dir)
        summary = run_pipeline(
            returns, rf, label=universe.label, out_tables=args.out / "tables" / universe.name,
            out_figures=args.out / "figures" / universe.name, estimator=args.estimator, n_sim=args.n_sim, seed=args.seed,
            n_points=args.n_points, n_boot=args.n_boot, window=args.window, cost_bps=args.cost_bps,
            descriptions=universe.descriptions,
        )
    else:
        returns, rf = synthetic_universe(n_assets=args.n_assets, n_months=args.n_months, seed=args.seed)
        summary = run_pipeline(
            returns, rf, label="univers synthétique (démo)", out_tables=args.out / "tables", out_figures=args.out / "figures",
            estimator=args.estimator, n_sim=args.n_sim, seed=args.seed, n_points=args.n_points, n_boot=args.n_boot,
            window=args.window, cost_bps=args.cost_bps, max_interactive_points=2_000,
        )
    _print_summary(summary, time.time() - t0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
