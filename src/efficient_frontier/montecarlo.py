"""Monte Carlo de portefeuilles aléatoires long-only et frontière rééchantillonnée de Michaud (1998).

Deux tirages de poids sont offerts :

* ``dirichlet`` : w ~ Dirichlet(1, ..., 1), loi uniforme sur le simplexe ; les coins (un actif à 100 %) et
  les arêtes sont visités avec leur poids géométrique naturel ;
* ``uniform`` : u ~ U(0, 1)^n normalisé par sa somme ; la loi se concentre autour de 1/n (le maximum d'un
  tirage normalisé dépasse rarement 2/n), donc le nuage est plus compact et n'atteint pas les portefeuilles
  concentrés qui forment les extrémités de la frontière.

Référence : Michaud, R. (1998), « Efficient Asset Management », Harvard Business School Press.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .estimation import estimate_moments
from .frontier import WEIGHT_PREFIX, Frontier, FrontierSolver, efficient_frontier, get_solver, portfolio_stats

SAMPLINGS = ("dirichlet", "uniform")


@dataclass
class MonteCarloResult:
    weights: np.ndarray  # (n_sim, n_assets)
    ret: np.ndarray
    vol: np.ndarray
    sharpe: np.ndarray
    sampling: str
    assets: list[str]
    rf: float

    @property
    def n_sim(self) -> int:
        return len(self.ret)

    def best_sharpe(self) -> int:
        return int(np.nanargmax(self.sharpe))

    def min_vol(self) -> int:
        return int(np.argmin(self.vol))


def random_weights(n_sim: int, n_assets: int, rng: np.random.Generator, sampling: str = "dirichlet") -> np.ndarray:
    if sampling == "dirichlet":
        return rng.dirichlet(np.ones(n_assets), size=n_sim)
    if sampling == "uniform":
        u = rng.random((n_sim, n_assets))
        return u / u.sum(axis=1, keepdims=True)
    raise ValueError(f"tirage inconnu : {sampling!r} (choix : {SAMPLINGS})")


def simulate_portfolios(mu, cov, n_sim: int = 50_000, seed: int = 123, sampling: str = "dirichlet", rf: float = 0.0) -> MonteCarloResult:
    """Rendement, volatilité et Sharpe de ``n_sim`` portefeuilles aléatoires, sans boucle Python."""
    mu_s = pd.Series(mu) if not isinstance(mu, pd.Series) else mu
    mu_a, cov_a = np.asarray(mu_s, dtype=float), np.asarray(cov, dtype=float)
    rng = np.random.default_rng(seed)
    w = random_weights(n_sim, len(mu_a), rng, sampling)
    ret = w @ mu_a
    var = np.einsum("ij,jk,ik->i", w, cov_a, w)
    vol = np.sqrt(np.clip(var, 0.0, None))
    sharpe = (ret - rf) / vol
    return MonteCarloResult(weights=w, ret=ret, vol=vol, sharpe=sharpe, sampling=sampling, assets=[str(a) for a in mu_s.index], rf=rf)


def gap_to_frontier(mc: MonteCarloResult, frontier: Frontier) -> np.ndarray:
    """Écart de volatilité entre chaque portefeuille simulé et la frontière au même rendement (>= 0 à la tolérance près)."""
    table = frontier.table.sort_values("ret")
    frontier_vol = np.interp(mc.ret, table["ret"].to_numpy(), table["vol"].to_numpy())
    return mc.vol - frontier_vol


def montecarlo_summary(mc: MonteCarloResult, frontier: Frontier, tangency: dict, min_var: dict) -> dict[str, float]:
    """Chiffres qui documentent la distance entre le nuage et la frontière analytique."""
    gap = gap_to_frontier(mc, frontier)
    max_w = mc.weights.max(axis=1)
    i_best, i_min = mc.best_sharpe(), mc.min_vol()
    return {
        "sampling": mc.sampling,
        "n_sim": mc.n_sim,
        "mc_best_sharpe": float(mc.sharpe[i_best]),
        "tangency_sharpe": tangency["sharpe"],
        "sharpe_gap": tangency["sharpe"] - float(mc.sharpe[i_best]),
        "mc_min_vol": float(mc.vol[i_min]),
        "min_var_vol": min_var["vol"],
        "mc_max_ret": float(mc.ret.max()),
        "frontier_max_ret": float(frontier.table["ret"].max()),
        "vol_gap_median": float(np.median(gap)),
        "vol_gap_p05": float(np.quantile(gap, 0.05)),
        "share_within_1pct_vol": float(np.mean(gap <= 0.01)),
        "max_weight_median": float(np.median(max_w)),
        "max_weight_p99": float(np.quantile(max_w, 0.99)),
        "share_max_weight_above_50pct": float(np.mean(max_w >= 0.5)),
    }


def resampled_frontier(
    returns: pd.DataFrame,
    n_boot: int = 200,
    n_points: int = 30,
    seed: int = 123,
    estimator: str = "sample",
    rf: float = 0.0,
    periods_per_year: int = 12,
    solver: FrontierSolver | None = None,
) -> pd.DataFrame:
    """Frontière rééchantillonnée (Michaud, 1998) : bootstrap i.i.d. des mois, ré-optimisation, moyenne des poids par rang.

    Chaque bootstrap tire T mois avec remise, ré-estime les moments, calcule ``n_points`` portefeuilles
    de la frontière long-only indexés par rang (du minimum de variance au rendement maximal), puis les poids
    de même rang sont moyennés. Les statistiques sont évaluées sous les moments d'origine : la frontière
    rééchantillonnée est donc toujours à l'intérieur de la frontière analytique.
    """
    rng = np.random.default_rng(seed)
    t = len(returns)
    assets = [str(c) for c in returns.columns]
    solver = solver or get_solver(len(assets))
    base = estimate_moments(returns, estimator, periods_per_year)
    sum_w = np.zeros((n_points, len(assets)))
    for _ in range(n_boot):
        idx = rng.integers(0, t, size=t)
        boot = returns.iloc[idx]
        m = estimate_moments(boot, estimator, periods_per_year)
        fr = efficient_frontier(m.mu, m.cov, n_points=n_points, rf=rf, solver=solver)
        sum_w += fr.weights
    avg_w = sum_w / n_boot
    rows = []
    for k in range(n_points):
        stats = portfolio_stats(avg_w[k], base.mu, base.cov, rf)
        rows.append({"rank": k, **stats, **{WEIGHT_PREFIX + a: avg_w[k, i] for i, a in enumerate(assets)}})
    return pd.DataFrame(rows)
