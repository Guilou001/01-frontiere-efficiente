"""Estimateurs des moments : échantillon, rétrécissement de Ledoit-Wolf (corrélation constante), annualisation.

Référence : Ledoit, O. et Wolf, M. (2004), « Honey, I Shrunk the Sample Covariance Matrix », Journal of
Portfolio Management 30(4), 110-119. Les formules de l'intensité suivent l'annexe du papier (code covCor.m).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ESTIMATORS = ("sample", "ledoit_wolf")


@dataclass
class Moments:
    """Moments annualisés prêts pour l'optimisation."""

    mu: pd.Series  # rendement espéré annualisé
    cov: pd.DataFrame  # covariance annualisée
    estimator: str
    shrinkage: float | None = None  # intensité de Ledoit-Wolf (None pour l'estimateur échantillon)
    n_obs: int = 0

    @property
    def assets(self) -> list[str]:
        return list(self.mu.index)

    @property
    def vol(self) -> pd.Series:
        return pd.Series(np.sqrt(np.diag(self.cov.values)), index=self.mu.index, name="vol")

    @property
    def corr(self) -> pd.DataFrame:
        d = 1.0 / self.vol.values
        return pd.DataFrame(self.cov.values * np.outer(d, d), index=self.mu.index, columns=self.mu.index)


def annualise_mean(mu_periodic, periods_per_year: int = 12):
    """Moyenne arithmétique par période vers moyenne annuelle (somme des périodes)."""
    return mu_periodic * periods_per_year


def annualise_cov(cov_periodic, periods_per_year: int = 12):
    """Covariance par période vers covariance annuelle (rendements supposés non autocorrélés)."""
    return cov_periodic * periods_per_year


def sample_moments(returns: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Moyenne et covariance échantillon (ddof = 1), par période."""
    return returns.mean(), returns.cov()


def ledoit_wolf_constant_correlation(returns: pd.DataFrame | np.ndarray) -> tuple[np.ndarray, float]:
    """Covariance rétrécie vers la cible à corrélation constante (Ledoit et Wolf, 2004).

    Retourne la matrice rétrécie (même échelle que la covariance échantillon, ddof = 1) et l'intensité
    delta dans [0, 1]. L'intensité est estimée avec la covariance en 1/T comme dans le papier ; elle est
    ensuite appliquée à la covariance ddof = 1 pour rester comparable à l'estimateur échantillon.
    """
    x = np.asarray(returns, dtype=float)
    t, n = x.shape
    x = x - x.mean(axis=0)
    sample = x.T @ x / t  # covariance en 1/T (convention du papier)
    var = np.diag(sample)
    sqrtvar = np.sqrt(var)
    outer_sd = np.outer(sqrtvar, sqrtvar)
    r_bar = (np.sum(sample / outer_sd) - n) / (n * (n - 1))
    prior = r_bar * outer_sd
    np.fill_diagonal(prior, var)

    # pi-hat : somme des variances asymptotiques des entrées de la covariance échantillon
    y = x**2
    phi_mat = (y.T @ y) / t - 2 * (x.T @ x) * sample / t + sample**2
    phi = phi_mat.sum()

    # rho-hat : covariances asymptotiques entre la cible et la covariance échantillon
    term1 = ((x**3).T @ x) / t
    help_ = x.T @ x / t
    help_diag = np.diag(help_)
    term2 = help_diag[:, None] * sample
    term3 = help_ * var[:, None]
    term4 = var[:, None] * sample
    theta_mat = term1 - term2 - term3 + term4
    np.fill_diagonal(theta_mat, 0.0)
    rho = np.trace(phi_mat) + r_bar * np.sum(np.outer(1.0 / sqrtvar, sqrtvar) * theta_mat)

    # gamma-hat : distance de Frobenius entre cible et échantillon
    gamma = np.linalg.norm(sample - prior, "fro") ** 2
    kappa = (phi - rho) / gamma if gamma > 0 else 0.0
    delta = float(min(1.0, max(0.0, kappa / t)))

    scale = t / (t - 1)
    shrunk = delta * prior * scale + (1 - delta) * sample * scale
    return shrunk, delta


def estimate_moments(returns: pd.DataFrame, estimator: str = "sample", periods_per_year: int = 12) -> Moments:
    """Moments annualisés selon l'estimateur choisi (« sample » ou « ledoit_wolf »)."""
    if estimator not in ESTIMATORS:
        raise ValueError(f"estimateur inconnu : {estimator!r} (choix : {ESTIMATORS})")
    mu_p, cov_p = sample_moments(returns)
    shrinkage = None
    if estimator == "ledoit_wolf":
        shrunk, shrinkage = ledoit_wolf_constant_correlation(returns)
        cov_p = pd.DataFrame(shrunk, index=returns.columns, columns=returns.columns)
    mu = annualise_mean(mu_p, periods_per_year).rename("mu")
    cov = annualise_cov(cov_p, periods_per_year)
    return Moments(mu=mu, cov=cov, estimator=estimator, shrinkage=shrinkage, n_obs=len(returns))
