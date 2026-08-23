"""Données synthétiques partagées (aucun accès réseau)."""

import pytest

from efficient_frontier.data import synthetic_universe
from efficient_frontier.estimation import estimate_moments


@pytest.fixture(scope="session")
def synthetic():
    returns, rf = synthetic_universe(n_assets=6, n_months=240, seed=0)
    return returns, rf


@pytest.fixture(scope="session")
def moments(synthetic):
    returns, _ = synthetic
    return estimate_moments(returns, "sample")
