"""Estimateurs : annualisation, Ledoit-Wolf (intensité dans [0, 1], matrice définie positive, rétrécissement effectif)."""

import numpy as np
import pandas as pd

from efficient_frontier.data import synthetic_universe
from efficient_frontier.estimation import (
    annualise_cov,
    annualise_mean,
    estimate_moments,
    ledoit_wolf_constant_correlation,
    sample_moments,
)


def test_annualisation_scales_mean_and_covariance():
    mu = pd.Series([0.01, 0.02])
    cov = pd.DataFrame([[0.01, 0.002], [0.002, 0.04]])
    assert annualise_mean(mu, 12).tolist() == [0.12, 0.24]
    np.testing.assert_allclose(annualise_cov(cov, 12).to_numpy(), cov.to_numpy() * 12)


def test_ledoit_wolf_intensity_in_unit_interval_and_positive_definite(synthetic):
    returns, _ = synthetic
    shrunk, delta = ledoit_wolf_constant_correlation(returns)
    assert 0.0 <= delta <= 1.0
    eigvals = np.linalg.eigvalsh(shrunk)
    assert eigvals.min() > 0
    np.testing.assert_allclose(shrunk, shrunk.T)
    # la diagonale (variances) est conservée, seule la structure hors diagonale est rétrécie
    _, cov_sample = sample_moments(returns)
    np.testing.assert_allclose(np.diag(shrunk), np.diag(cov_sample.to_numpy()), rtol=1e-10)


def test_ledoit_wolf_reduces_dispersion_of_correlations(synthetic):
    returns, _ = synthetic
    m_s = estimate_moments(returns, "sample")
    m_lw = estimate_moments(returns, "ledoit_wolf")
    off = ~np.eye(len(m_s.mu), dtype=bool)
    assert m_lw.corr.to_numpy()[off].std() < m_s.corr.to_numpy()[off].std()
    assert m_lw.shrinkage is not None and m_s.shrinkage is None


def test_ledoit_wolf_intensity_falls_with_sample_size_when_target_is_misspecified():
    # corrélations hétérogènes (modèle à un facteur avec bêtas différents) : la cible à corrélation constante est
    # fausse, donc l'intensité optimale décroît quand l'échantillon grandit
    short, _ = synthetic_universe(n_assets=6, n_months=36, seed=1)
    long, _ = synthetic_universe(n_assets=6, n_months=3000, seed=1)
    _, delta_short = ledoit_wolf_constant_correlation(short)
    _, delta_long = ledoit_wolf_constant_correlation(long)
    assert delta_short > delta_long
    assert delta_long < 0.2
