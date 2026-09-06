"""Pipeline complet : moments -> frontière -> portefeuilles remarquables -> Monte Carlo -> rééchantillonnage -> backtest -> figures."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import plots
from .backtest import STRATEGIES, metrics_table, walk_forward
from .estimation import ESTIMATORS, estimate_moments
from .finquant_bridge import compare_finquant
from .frontier import (
    WEIGHT_PREFIX,
    closed_form_frontier,
    efficient_frontier,
    equal_weights,
    get_solver,
    inverse_vol_weights,
    portfolio_stats,
)
from .montecarlo import SAMPLINGS, montecarlo_summary, resampled_frontier, simulate_portfolios


def annual_rf(rf_monthly: pd.Series, periods_per_year: int = 12) -> float:
    return float((1.0 + rf_monthly.mean()) ** periods_per_year - 1.0)


def run_pipeline(
    returns: pd.DataFrame,
    rf: pd.Series,
    label: str,
    out_tables: Path,
    out_figures: Path,
    estimator: str = "sample",
    n_sim: int = 50_000,
    seed: int = 123,
    n_points: int = 60,
    n_boot: int = 200,
    window: int = 60,
    cost_bps: float = 10.0,
    descriptions: dict[str, str] | None = None,
    periods_per_year: int = 12,
    max_interactive_points: int = 3_000,
) -> dict:
    """Écrit tables (CSV, JSON) et figures (PNG, PDF, HTML) ; renvoie le résumé chiffré."""
    out_tables.mkdir(parents=True, exist_ok=True)
    out_figures.mkdir(parents=True, exist_ok=True)
    plots.use_style()
    tag = estimator
    assets = [str(c) for c in returns.columns]
    n = len(assets)
    rf_a = annual_rf(rf, periods_per_year)
    period = f"{returns.index[0]:%Y-%m} à {returns.index[-1]:%Y-%m}"
    title_base = f"{label}, {period}, estimateur {plots.ESTIMATOR_LABELS[estimator]}"

    # 1. moments
    m = estimate_moments(returns, estimator, periods_per_year)
    moments = pd.DataFrame({"asset": assets, "description": [(descriptions or {}).get(a, "") for a in assets],
                            "mean_annual": m.mu.values, "vol_annual": m.vol.values})
    moments["sharpe_annual"] = (moments["mean_annual"] - rf_a) / moments["vol_annual"]
    moments.to_csv(out_tables / f"moments_{tag}.csv", index=False, float_format="%.6f")
    m.corr.round(4).to_csv(out_tables / f"correlation_{tag}.csv")

    # 2. frontière long-only + forme fermée sans contrainte
    solver = get_solver(n)
    fr = efficient_frontier(m.mu, m.cov, n_points=n_points, rf=rf_a, solver=solver)
    w_unc = closed_form_frontier(m.mu, m.cov, fr.table["target_return"].to_numpy())
    fr.table["vol_unconstrained"] = np.sqrt(np.einsum("ij,jk,ik->i", w_unc, m.cov.values, w_unc))
    fr.table.to_csv(out_tables / f"frontier_{tag}.csv", index=False, float_format="%.6f")
    unconstrained = pd.DataFrame({"ret": fr.table["target_return"], "vol": fr.table["vol_unconstrained"]})
    finquant_check = compare_finquant(m.mu, m.cov, rf_a, fr)
    finquant_check.to_csv(out_tables / f"finquant_check_{tag}.csv", index=False, float_format="%.10f")

    # 3. portefeuilles remarquables
    weights = {
        "min_variance": solver.min_variance(m.cov.values),
        "tangency": solver.tangency(m.mu.values, m.cov.values, rf_a),
        "max_diversification": solver.max_diversification(m.cov.values),
        "inverse_vol": inverse_vol_weights(m.cov.values),
        "equal_weight": equal_weights(n),
    }
    special = {k: portfolio_stats(w, m.mu.values, m.cov.values, rf_a) for k, w in weights.items()}
    rows = [{"portfolio": k, **special[k], **{WEIGHT_PREFIX + a: weights[k][i] for i, a in enumerate(assets)}} for k in weights]
    pd.DataFrame(rows).to_csv(out_tables / f"special_portfolios_{tag}.csv", index=False, float_format="%.6f")
    asset_stats = pd.DataFrame({"ret": m.mu.values, "vol": m.vol.values}, index=assets)

    # 4. Monte Carlo (deux tirages)
    mc_results = {s: simulate_portfolios(m.mu, m.cov, n_sim=n_sim, seed=seed, sampling=s, rf=rf_a) for s in SAMPLINGS}
    mc_summary = pd.DataFrame([montecarlo_summary(mc_results[s], fr, special["tangency"], special["min_variance"]) for s in SAMPLINGS])
    mc_summary.to_csv(out_tables / f"montecarlo_summary_{tag}.csv", index=False, float_format="%.6f")

    # 5. frontière rééchantillonnée
    rs = resampled_frontier(returns, n_boot=n_boot, n_points=max(10, n_points // 2), seed=seed, estimator=estimator, rf=rf_a,
                            periods_per_year=periods_per_year, solver=solver)
    rs.to_csv(out_tables / f"resampled_frontier_{tag}.csv", index=False, float_format="%.6f")

    # 6. backtest glissant, deux estimateurs (les règles 1/N et inverse-vol ne dépendent pas de l'estimateur)
    backtests = {est: walk_forward(returns, rf, window=window, estimator=est, cost_bps=cost_bps, strategies=STRATEGIES,
                                   periods_per_year=periods_per_year) for est in ESTIMATORS}
    metrics = []
    for est, bt in backtests.items():
        tbl = metrics_table(bt, periods_per_year)
        if est != "sample":
            tbl = tbl[tbl["estimator"] != "aucun"]
        metrics.append(tbl)
    oos = pd.concat(metrics, ignore_index=True)
    oos.insert(0, "period", f"{backtests['sample'].returns_net.index[0]:%Y-%m} à {backtests['sample'].returns_net.index[-1]:%Y-%m}")
    oos.to_csv(out_tables / "oos_metrics.csv", index=False, float_format="%.6f")
    oos_returns = pd.concat({est: bt.returns_net for est, bt in backtests.items()}, axis=1)
    oos_returns.columns = [f"{s}__{est}" for est, s in oos_returns.columns]
    oos_returns.to_csv(out_tables / "oos_returns.csv", float_format="%.6f")
    # Entrées de l'inférence conservées sans l'arrondi à six décimales des tables historiques.
    inference_inputs = pd.DataFrame({
        **{f"max_sharpe__{est}": bt.returns_net["max_sharpe"] for est, bt in backtests.items()},
        "equal_weight": backtests["sample"].returns_net["equal_weight"],
        "rf": backtests["sample"].rf,
    })
    inference_inputs.to_csv(out_tables / "oos_inference_inputs.csv", index_label="date", float_format="%.17g")

    # 7. figures
    figs: dict[str, list[str]] = {}
    n_sim_txt = f"{n_sim:,}".replace(",", " ")
    for s, mc in mc_results.items():
        figs[f"cloud_{s}"] = [str(p) for p in plots.plot_cloud(
            mc, fr, special, asset_stats, rf_a, out_figures / f"cloud_{s}_{tag}",
            title=f"{title_base}\n{n_sim_txt} portefeuilles aléatoires, {plots.SAMPLING_LABELS[s]}",
            unconstrained=unconstrained, finquant_check=finquant_check)]
    figs["transition_map"] = [str(p) for p in plots.plot_transition_map(
        fr, out_figures / f"transition_map_{tag}", title=f"Carte de transition de la frontière long-only\n{title_base}",
        markers={"var. min.": special["min_variance"]["vol"], "tangence": special["tangency"]["vol"]})]
    figs["corr_heatmap"] = [str(p) for p in plots.plot_corr_heatmap(m.corr, out_figures / f"corr_heatmap_{tag}",
                                                                     title=f"Corrélations, {title_base}")]
    figs["resampled"] = [str(p) for p in plots.plot_resampled_vs_analytical(
        fr, rs, out_figures / f"resampled_vs_analytical_{tag}", title=f"Frontière rééchantillonnée contre analytique, {title_base}", n_boot=n_boot)]
    figs["oos_growth"] = [str(p) for p in plots.plot_oos_growth(
        {est: bt.returns_net for est, bt in backtests.items()}, out_figures / "oos_growth",
        title=f"Hors échantillon, fenêtre {window} mois, rééquilibrage mensuel\n{label}, {oos['period'].iloc[0]}", cost_bps=cost_bps)]
    figs["oos_weights"] = [str(p) for p in plots.plot_rolling_weights(
        backtests[estimator].weights, out_figures / f"oos_weights_{tag}",
        title=f"Poids glissants hors échantillon, {label}, {oos['period'].iloc[0]}, "
              f"estimateur {plots.ESTIMATOR_LABELS[estimator]}")]
    figs["interactive"] = [str(plots.plotly_cloud(mc_results["dirichlet"], fr, special, asset_stats, rf_a,
                                                   out_figures / f"cloud_interactive_{tag}.html", title=title_base,
                                                   max_points=max_interactive_points, seed=seed))]

    # 8. résumé
    oos_idx = oos.set_index(["strategy", "estimator"])
    summary = {
        "label": label,
        "estimator": estimator,
        "n_assets": n,
        "assets": assets,
        "period": period,
        "n_months": int(len(returns)),
        "rf_annual_mean": rf_a,
        "shrinkage": m.shrinkage,
        "n_sim": n_sim,
        "seed": seed,
        "n_boot": n_boot,
        "special_portfolios": special,
        "montecarlo": mc_summary.to_dict(orient="records"),
        "oos_period": oos["period"].iloc[0],
        "oos_sharpe": {f"{s}/{e}": float(v) for (s, e), v in oos_idx["sharpe"].items()},
        "figures": figs,
    }
    (out_tables / f"summary_{tag}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    return summary
