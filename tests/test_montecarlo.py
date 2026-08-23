"""Monte Carlo : poids admissibles, tangence dominante, écart à la frontière, tirages Dirichlet et uniforme, rééchantillonnage."""

import numpy as np
import pytest

from efficient_frontier.frontier import efficient_frontier, portfolio_stats, tangency_weights
from efficient_frontier.montecarlo import gap_to_frontier, random_weights, resampled_frontier, simulate_portfolios


@pytest.mark.parametrize("sampling", ["dirichlet", "uniform"])
def test_random_weights_sum_to_one_and_are_nonnegative(sampling):
    rng = np.random.default_rng(0)
    w = random_weights(5000, 7, rng, sampling)
    assert w.shape == (5000, 7)
    np.testing.assert_allclose(w.sum(axis=1), 1.0, atol=1e-12)
    assert (w >= 0).all()


def test_uniform_normalised_is_more_concentrated_around_one_over_n_than_dirichlet():
    rng = np.random.default_rng(0)
    w_d = random_weights(20000, 8, rng, "dirichlet")
    w_u = random_weights(20000, 8, rng, "uniform")
    assert w_u.max(axis=1).mean() < w_d.max(axis=1).mean()
    assert np.quantile(w_u.max(axis=1), 0.99) < np.quantile(w_d.max(axis=1), 0.99)


def test_tangency_sharpe_dominates_every_simulated_portfolio(moments):
    rf = 0.02
    mc = simulate_portfolios(moments.mu, moments.cov, n_sim=20000, seed=1, sampling="dirichlet", rf=rf)
    w_t = tangency_weights(moments.mu, moments.cov, rf)
    s_t = portfolio_stats(w_t, moments.mu, moments.cov, rf)["sharpe"]
    assert s_t >= np.nanmax(mc.sharpe) - 1e-6
    assert mc.n_sim == 20000 and mc.weights.shape == (20000, len(moments.mu))
    np.testing.assert_allclose(mc.ret, mc.weights @ moments.mu.to_numpy())


def test_simulated_portfolios_lie_on_or_inside_the_frontier(moments):
    fr = efficient_frontier(moments.mu, moments.cov, n_points=60)
    mc = simulate_portfolios(moments.mu, moments.cov, n_sim=10000, seed=2)
    gap = gap_to_frontier(mc, fr)
    assert gap.min() >= -2e-3  # tolérance d'interpolation linéaire entre points de la frontière


def test_simulation_is_reproducible_with_seed(moments):
    a = simulate_portfolios(moments.mu, moments.cov, n_sim=100, seed=7)
    b = simulate_portfolios(moments.mu, moments.cov, n_sim=100, seed=7)
    np.testing.assert_array_equal(a.weights, b.weights)


def test_resampled_frontier_is_inside_analytical_frontier(synthetic):
    returns, _ = synthetic
    from efficient_frontier.estimation import estimate_moments

    m = estimate_moments(returns, "sample")
    fr = efficient_frontier(m.mu, m.cov, n_points=15)
    rs = resampled_frontier(returns, n_boot=10, n_points=15, seed=3)
    w = rs[[c for c in rs.columns if c.startswith("w_")]].to_numpy()
    np.testing.assert_allclose(w.sum(axis=1), 1.0, atol=1e-8)
    assert (w >= 0).all()
    frontier_vol = np.interp(rs["ret"], fr.table["ret"], fr.table["vol"])
    assert (rs["vol"].to_numpy() >= frontier_vol - 2e-3).all()
