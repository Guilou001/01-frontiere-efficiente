"""Frontière : poids admissibles, volatilité croissante avec la cible, variance minimale, tangence, forme fermée, CML."""

import numpy as np
import pandas as pd

from efficient_frontier.frontier import (
    capital_market_line,
    closed_form_frontier,
    closed_form_min_variance,
    closed_form_tangency,
    efficient_frontier,
    max_diversification_weights,
    min_variance_weights,
    portfolio_stats,
    tangency_weights,
)


def test_frontier_weights_sum_to_one_and_are_nonnegative(moments):
    fr = efficient_frontier(moments.mu, moments.cov, n_points=25, rf=0.02)
    w = fr.weights
    np.testing.assert_allclose(w.sum(axis=1), 1.0, atol=1e-8)
    assert (w >= 0).all()
    assert list(fr.table.columns[:4]) == ["target_return", "ret", "vol", "sharpe"]


def test_frontier_volatility_is_nondecreasing_in_target_return(moments):
    fr = efficient_frontier(moments.mu, moments.cov, n_points=40)
    vol = fr.table["vol"].to_numpy()
    assert (np.diff(vol) >= -1e-7).all()
    assert (np.diff(fr.table["target_return"].to_numpy()) > 0).all()


def test_min_variance_has_lowest_volatility_among_random_portfolios(moments):
    w_min = min_variance_weights(moments.cov)
    v_min = portfolio_stats(w_min, moments.mu, moments.cov)["vol"]
    rng = np.random.default_rng(0)
    w = rng.dirichlet(np.ones(len(w_min)), size=2000)
    vols = np.sqrt(np.einsum("ij,jk,ik->i", w, moments.cov.to_numpy(), w))
    assert v_min <= vols.min() + 1e-8


def test_tangency_beats_any_frontier_point_on_sharpe(moments):
    rf = 0.02
    fr = efficient_frontier(moments.mu, moments.cov, n_points=40, rf=rf)
    w_t = tangency_weights(moments.mu, moments.cov, rf)
    s_t = portfolio_stats(w_t, moments.mu, moments.cov, rf)["sharpe"]
    assert s_t >= fr.table["sharpe"].max() - 1e-6
    np.testing.assert_allclose(w_t.sum(), 1.0, atol=1e-8)
    assert (w_t >= 0).all()


def test_closed_form_matches_qp_when_unconstrained_solution_is_long_only():
    # actifs non corrélés de même variance : la variance minimale est 1/N dans les deux versions
    n = 5
    cov = pd.DataFrame(np.eye(n) * 0.04)
    mu = pd.Series(np.linspace(0.03, 0.07, n))
    np.testing.assert_allclose(closed_form_min_variance(cov), np.full(n, 0.2), atol=1e-8)
    np.testing.assert_allclose(min_variance_weights(cov), np.full(n, 0.2), atol=1e-6)
    # sur la frontière fermée, un point de cible égale au rendement de 1/N redonne 1/N
    w = closed_form_frontier(mu, cov, [mu.mean()])
    np.testing.assert_allclose(w[0], np.full(n, 0.2), atol=1e-8)
    # tangence fermée : w proportionnel à Σ⁻¹(mu - rf) ; ici proportionnel à mu - rf
    rf = 0.01
    expected = (mu - rf) / (mu - rf).sum()
    np.testing.assert_allclose(closed_form_tangency(mu, cov, rf), expected, atol=1e-10)
    np.testing.assert_allclose(tangency_weights(mu, cov, rf), expected, atol=1e-5)


def test_unconstrained_frontier_dominates_long_only(moments):
    fr = efficient_frontier(moments.mu, moments.cov, n_points=20)
    w_unc = closed_form_frontier(moments.mu, moments.cov, fr.table["target_return"])
    vol_unc = np.sqrt(np.einsum("ij,jk,ik->i", w_unc, moments.cov.to_numpy(), w_unc))
    assert (vol_unc <= fr.table["vol"].to_numpy() + 1e-8).all()


def test_capital_market_line_passes_through_rf_and_tangency():
    line = capital_market_line(0.02, 0.10, 0.16, [0.0, 0.16, 0.32])
    np.testing.assert_allclose(line, [0.02, 0.10, 0.18])


def test_max_diversification_weights_are_valid(moments):
    w = max_diversification_weights(moments.cov)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-8)
    assert (w >= 0).all()
    # ratio de diversification >= celui de 1/N
    sig = np.sqrt(np.diag(moments.cov.to_numpy()))
    def ratio(x):
        return (x @ sig) / portfolio_stats(x, moments.mu, moments.cov)["vol"]
    assert ratio(w) >= ratio(np.full(len(w), 1 / len(w))) - 1e-8


def test_tangency_falls_back_to_min_variance_when_no_asset_beats_rf(moments):
    rf = float(moments.mu.max()) + 0.01
    w = tangency_weights(moments.mu, moments.cov, rf)
    np.testing.assert_allclose(w, min_variance_weights(moments.cov), atol=1e-6)
