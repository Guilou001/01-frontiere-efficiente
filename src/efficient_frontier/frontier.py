"""Frontière efficiente de Markowitz : programme quadratique long-only (cvxpy) et forme fermée sans contrainte.

Conventions : ``mu`` et ``cov`` sont annualisés ; les poids somment à 1. Les problèmes long-only sont compilés
une fois avec des paramètres (DPP) et résolus par Clarabel, ce qui rend les milliers de résolutions de la
frontière rééchantillonnée et du backtest glissant bon marché.
"""

from __future__ import annotations

from dataclasses import dataclass

import cvxpy as cp
import numpy as np
import pandas as pd

SOLVER = cp.CLARABEL
WEIGHT_PREFIX = "w_"


def _as_array(x) -> np.ndarray:
    return np.asarray(x, dtype=float)


def sqrt_factor(cov: np.ndarray) -> np.ndarray:
    """Matrice L telle que L.T @ L = cov (décomposition spectrale, tolère une matrice semi-définie)."""
    vals, vecs = np.linalg.eigh(_as_array(cov))
    vals = np.clip(vals, 0.0, None)
    return (np.sqrt(vals)[:, None] * vecs.T)


def portfolio_stats(w, mu, cov, rf: float = 0.0) -> dict[str, float]:
    """Rendement espéré, volatilité et ratio de Sharpe annualisés d'un vecteur de poids."""
    w, mu, cov = _as_array(w), _as_array(mu), _as_array(cov)
    ret = float(w @ mu)
    vol = float(np.sqrt(max(w @ cov @ w, 0.0)))
    sharpe = (ret - rf) / vol if vol > 0 else np.nan
    return {"ret": ret, "vol": vol, "sharpe": sharpe}


class FrontierSolver:
    """Trois programmes quadratiques long-only compilés une fois pour ``n`` actifs.

    * variance minimale : min w'Σw, 1'w = 1, w >= 0 ;
    * variance minimale à rendement cible : idem + mu'w = cible ;
    * tangence (Sharpe maximal) : min y'Σy, (mu - rf)'y = 1, y >= 0, puis w = y / 1'y
      (transformation de Charnes-Cooper ; exige qu'un actif au moins ait mu > rf).
    """

    def __init__(self, n: int):
        self.n = n
        self.w = cp.Variable(n)
        self.y = cp.Variable(n)
        self.L = cp.Parameter((n, n))
        self.mu = cp.Parameter(n)
        self.mu_ex = cp.Parameter(n)
        self.target = cp.Parameter()
        self.aux = cp.Parameter(n, nonneg=True)  # vecteur auxiliaire (volatilités) pour la diversification max
        risk_w = cp.sum_squares(self.L @ self.w)
        base = [cp.sum(self.w) == 1, self.w >= 0]
        self._min_var = cp.Problem(cp.Minimize(risk_w), base)
        self._target = cp.Problem(cp.Minimize(risk_w), [*base, self.mu @ self.w == self.target])
        risk_y = cp.sum_squares(self.L @ self.y)
        self._tangency = cp.Problem(cp.Minimize(risk_y), [self.mu_ex @ self.y == 1, self.y >= 0])
        self._max_div = cp.Problem(cp.Minimize(risk_y), [self.aux @ self.y == 1, self.y >= 0])

    def set_cov(self, cov) -> None:
        self.L.value = sqrt_factor(cov)

    def _solve(self, problem: cp.Problem) -> np.ndarray:
        problem.solve(solver=SOLVER)
        if problem.status not in ("optimal", "optimal_inaccurate"):
            raise RuntimeError(f"QP non résolu : statut {problem.status}")
        var = self.w if problem in (self._min_var, self._target) else self.y
        x = np.clip(np.asarray(var.value, dtype=float).ravel(), 0.0, None)
        return x / x.sum()

    def min_variance(self, cov) -> np.ndarray:
        self.set_cov(cov)
        return self._solve(self._min_var)

    def target_return(self, mu, cov, target: float) -> np.ndarray:
        self.set_cov(cov)
        self.mu.value = _as_array(mu)
        self.target.value = float(target)
        return self._solve(self._target)

    def tangency(self, mu, cov, rf: float) -> np.ndarray:
        mu = _as_array(mu)
        if mu.max() <= rf:
            # aucun actif ne bat le taux sans risque : le portefeuille de tangence n'existe pas en long-only,
            # on renvoie la variance minimale (documenté dans le README, section Limites)
            return self.min_variance(cov)
        self.set_cov(cov)
        self.mu_ex.value = mu - rf
        return self._solve(self._tangency)

    def max_diversification(self, cov) -> np.ndarray:
        """Maximise (w'σ) / sqrt(w'Σw), Choueifaty et Coignard (2008), même transformation que la tangence."""
        self.set_cov(cov)
        self.aux.value = np.sqrt(np.diag(_as_array(cov)))
        return self._solve(self._max_div)


_SOLVERS: dict[int, FrontierSolver] = {}


def get_solver(n: int) -> FrontierSolver:
    if n not in _SOLVERS:
        _SOLVERS[n] = FrontierSolver(n)
    return _SOLVERS[n]


def min_variance_weights(cov) -> np.ndarray:
    return get_solver(len(cov)).min_variance(cov)


def tangency_weights(mu, cov, rf: float) -> np.ndarray:
    return get_solver(len(mu)).tangency(mu, cov, rf)


def max_diversification_weights(cov) -> np.ndarray:
    return get_solver(len(cov)).max_diversification(cov)


def equal_weights(n: int) -> np.ndarray:
    return np.full(n, 1.0 / n)


def inverse_vol_weights(cov) -> np.ndarray:
    inv = 1.0 / np.sqrt(np.diag(_as_array(cov)))
    return inv / inv.sum()


@dataclass
class Frontier:
    """Points de la frontière long-only : statistiques et poids (une ligne par rendement cible)."""

    table: pd.DataFrame  # colonnes : target_return, ret, vol, sharpe, w_<actif>...
    assets: list[str]

    @property
    def weights(self) -> np.ndarray:
        return self.table[[WEIGHT_PREFIX + a for a in self.assets]].to_numpy()


def efficient_frontier(mu, cov, n_points: int = 50, rf: float = 0.0, solver: FrontierSolver | None = None) -> Frontier:
    """Frontière long-only : ``n_points`` cibles de rendement entre la variance minimale et l'actif le plus rentable."""
    mu_s = pd.Series(mu) if not isinstance(mu, pd.Series) else mu
    assets = [str(a) for a in mu_s.index]
    mu_a, cov_a = _as_array(mu_s), _as_array(cov)
    solver = solver or get_solver(len(assets))
    w_min = solver.min_variance(cov_a)
    r_min = float(w_min @ mu_a)
    targets = np.linspace(r_min, mu_a.max(), n_points)
    rows = []
    for k, tgt in enumerate(targets):
        w = w_min if k == 0 else solver.target_return(mu_a, cov_a, tgt)
        stats = portfolio_stats(w, mu_a, cov_a, rf)
        rows.append({"target_return": tgt, **stats, **{WEIGHT_PREFIX + a: w[i] for i, a in enumerate(assets)}})
    return Frontier(table=pd.DataFrame(rows), assets=assets)


def capital_market_line(rf: float, tangency_ret: float, tangency_vol: float, vols) -> np.ndarray:
    """Rendement espéré sur la droite de marché des capitaux aux volatilités ``vols`` (Sharpe, 1964)."""
    return rf + (tangency_ret - rf) / tangency_vol * _as_array(vols)


# ---------------------------------------------------------------------------------------------------------------
# Forme fermée sans contrainte de signe (Merton, 1972) : théorème des deux fonds
# ---------------------------------------------------------------------------------------------------------------


def closed_form_frontier(mu, cov, target_returns) -> np.ndarray:
    """Poids de variance minimale pour chaque rendement cible, ventes à découvert permises.

    w(m) = g + h m avec g = (B Σ⁻¹1 - A Σ⁻¹mu) / D, h = (C Σ⁻¹mu - A Σ⁻¹1) / D, où A = 1'Σ⁻¹mu,
    B = mu'Σ⁻¹mu, C = 1'Σ⁻¹1, D = BC - A². Toute frontière est une combinaison de deux de ses points.
    """
    mu, cov = _as_array(mu), _as_array(cov)
    ones = np.ones_like(mu)
    inv_mu = np.linalg.solve(cov, mu)
    inv_one = np.linalg.solve(cov, ones)
    a, b, c = ones @ inv_mu, mu @ inv_mu, ones @ inv_one
    d = b * c - a * a
    g = (b * inv_one - a * inv_mu) / d
    h = (c * inv_mu - a * inv_one) / d
    m = _as_array(target_returns).reshape(-1, 1)
    return g[None, :] + m * h[None, :]


def closed_form_min_variance(cov) -> np.ndarray:
    cov = _as_array(cov)
    inv_one = np.linalg.solve(cov, np.ones(len(cov)))
    return inv_one / inv_one.sum()


def closed_form_tangency(mu, cov, rf: float) -> np.ndarray:
    """w ∝ Σ⁻¹(mu - rf), normalisé à 1 (suppose 1'Σ⁻¹(mu - rf) > 0)."""
    mu, cov = _as_array(mu), _as_array(cov)
    x = np.linalg.solve(cov, mu - rf)
    return x / x.sum()
