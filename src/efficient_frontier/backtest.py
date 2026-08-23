"""Backtest glissant hors échantillon : quatre règles de pondération, fenêtre de 60 mois, rééquilibrage mensuel, coûts.

À la fin de chaque mois t, les moments sont estimés sur les ``window`` mois précédents (t inclus), les poids
cibles sont fixés et tenus pendant le mois t+1. Les coûts sont de ``cost_bps`` points de base par unité de
rotation aller simple (somme des |poids cible - poids dérivé|). Les poids dérivent avec les rendements entre
deux rééquilibrages.

Référence pour la comparaison à 1/N : DeMiguel, Garlappi et Uppal (2009), Review of Financial Studies 22(5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .estimation import estimate_moments
from .frontier import equal_weights, get_solver, inverse_vol_weights

STRATEGIES = ("max_sharpe", "min_variance", "inverse_vol", "equal_weight")
STRATEGY_LABELS = {
    "max_sharpe": "Sharpe maximal (tangence)",
    "min_variance": "Variance minimale",
    "inverse_vol": "Inverse de la volatilité",
    "equal_weight": "Équipondéré (1/N)",
}
ESTIMATOR_FREE = ("inverse_vol", "equal_weight")  # règles identiques quel que soit l'estimateur de covariance


def target_weights(strategy: str, window_returns: pd.DataFrame, rf_window: pd.Series, estimator: str, periods_per_year: int = 12) -> np.ndarray:
    n = window_returns.shape[1]
    if strategy == "equal_weight":
        return equal_weights(n)
    m = estimate_moments(window_returns, estimator, periods_per_year)
    if strategy == "inverse_vol":
        return inverse_vol_weights(m.cov)
    solver = get_solver(n)
    if strategy == "min_variance":
        return solver.min_variance(m.cov.values)
    if strategy == "max_sharpe":
        rf_annual = (1.0 + float(rf_window.mean())) ** periods_per_year - 1.0
        return solver.tangency(m.mu.values, m.cov.values, rf_annual)
    raise ValueError(f"stratégie inconnue : {strategy!r} (choix : {STRATEGIES})")


@dataclass
class BacktestResult:
    returns_net: pd.DataFrame  # une colonne par stratégie
    returns_gross: pd.DataFrame
    turnover: pd.DataFrame  # rotation aller simple par mois
    weights: dict[str, pd.DataFrame] = field(default_factory=dict)  # poids cibles par date de rééquilibrage
    rf: pd.Series | None = None
    estimator: str = "sample"
    window: int = 60
    cost_bps: float = 10.0


def walk_forward(
    returns: pd.DataFrame,
    rf: pd.Series,
    window: int = 60,
    estimator: str = "sample",
    cost_bps: float = 10.0,
    strategies: tuple[str, ...] = STRATEGIES,
    periods_per_year: int = 12,
) -> BacktestResult:
    """Rendements nets mensuels hors échantillon des stratégies, à partir du mois ``window``."""
    if len(returns) <= window:
        raise ValueError(f"il faut plus de {window} mois de rendements (reçu {len(returns)})")
    cost_rate = cost_bps / 1e4
    dates = returns.index[window:]
    n = returns.shape[1]
    rets_net = {s: [] for s in strategies}
    rets_gross = {s: [] for s in strategies}
    turn = {s: [] for s in strategies}
    weights = {s: [] for s in strategies}
    drift = {s: np.zeros(n) for s in strategies}  # portefeuille vide avant le premier achat
    r_all = returns.to_numpy()
    for t in range(window, len(returns)):
        win = returns.iloc[t - window : t]
        rf_win = rf.iloc[t - window : t]
        r_next = r_all[t]
        for s in strategies:
            w = target_weights(s, win, rf_win, estimator, periods_per_year)
            to = float(np.abs(w - drift[s]).sum())
            gross = float(w @ r_next)
            rets_gross[s].append(gross)
            rets_net[s].append(gross - cost_rate * to)
            turn[s].append(to)
            weights[s].append(w)
            drift[s] = w * (1.0 + r_next) / (1.0 + gross)
    cols = list(returns.columns)
    return BacktestResult(
        returns_net=pd.DataFrame(rets_net, index=dates),
        returns_gross=pd.DataFrame(rets_gross, index=dates),
        turnover=pd.DataFrame(turn, index=dates),
        weights={s: pd.DataFrame(np.vstack(weights[s]), index=dates, columns=cols) for s in strategies},
        rf=rf.loc[dates],
        estimator=estimator,
        window=window,
        cost_bps=cost_bps,
    )


def max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns).cumprod()
    peak = wealth.cummax()
    return float((wealth / peak - 1.0).min())


def performance_metrics(returns: pd.Series, rf: pd.Series, turnover: pd.Series | None = None, periods_per_year: int = 12) -> dict[str, float]:
    """TCAC en années civiles, volatilité et Sharpe annualisés, perte maximale, rotation annuelle moyenne."""
    returns = returns.dropna()
    wealth = float((1.0 + returns).prod())
    start = returns.index[0] - pd.offsets.MonthEnd(1)  # le premier rendement couvre le premier mois entier
    years = (returns.index[-1] - start).days / 365.25
    excess = returns - rf.reindex(returns.index)
    vol = float(returns.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe = float(excess.mean() / excess.std(ddof=1) * np.sqrt(periods_per_year)) if excess.std(ddof=1) > 0 else np.nan
    out = {
        "n_months": int(len(returns)),
        "cagr": wealth ** (1.0 / years) - 1.0,
        "vol": vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(returns),
        "final_wealth": wealth,
    }
    if turnover is not None:
        out["turnover_annual"] = float(turnover.reindex(returns.index).mean() * periods_per_year)
    return out


def metrics_table(result: BacktestResult, periods_per_year: int = 12) -> pd.DataFrame:
    rows = []
    for s in result.returns_net.columns:
        m = performance_metrics(result.returns_net[s], result.rf, result.turnover[s], periods_per_year)
        rows.append({"strategy": s, "estimator": "aucun" if s in ESTIMATOR_FREE else result.estimator, **m})
    return pd.DataFrame(rows)
