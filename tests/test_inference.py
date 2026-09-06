"""Oracles de blocs, appariement et conventions de Sharpe."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from efficient_frontier.backtest import performance_metrics
from efficient_frontier.inference import circular_indices, paired_sharpe_bootstrap, sharpe_difference


def series():
    dates = pd.date_range("2020-01-31", periods=48, freq="ME")
    rng = np.random.default_rng(74)
    rf = pd.Series(np.linspace(0.0001, 0.004, len(dates)), index=dates)
    a = pd.Series(rng.normal(0.007, 0.04, len(dates)), index=dates)
    b = pd.Series(rng.normal(0.005, 0.03, len(dates)), index=dates)
    return a, b, rf


def test_circular_wrap_and_truncated_last_block():
    # n=7, trois blocs de 3, départs imposés 5, 1, 6 : le dernier garde un mois.
    class Starts:
        def integers(self, low, high, size):
            assert (low, high, size) == (0, 7, (1, 3))
            return np.array([[5, 1, 6]])

    np.testing.assert_array_equal(circular_indices(7, 3, 1, Starts()), [[5, 6, 0, 1, 2, 3, 6]])


def test_sharpe_annualization_against_hand_calculation_and_existing_metrics():
    # Moyenne A=2, écart type A=1 ; moyenne B=2, écart type B=2.
    assert sharpe_difference([[1, 0], [2, 2], [3, 4]]) == pytest.approx(np.sqrt(12))
    a, b, rf = series()
    actual = sharpe_difference(np.column_stack([a - rf, b - rf]))
    expected = performance_metrics(a, rf)["sharpe"] - performance_metrics(b, rf)["sharpe"]
    assert actual == pytest.approx(expected, abs=1e-14)


def test_identical_series_have_exact_zero_interval_and_swapping_reverses_bounds():
    a, b, rf = series()
    zero = paired_sharpe_bootstrap(a, a, rf, n_boot=200)
    np.testing.assert_array_equal(zero[["sharpe_difference", "ci_low", "ci_high", "bootstrap_se"]], 0)
    forward = paired_sharpe_bootstrap(a, b, rf, n_boot=200)
    reverse = paired_sharpe_bootstrap(b, a, rf, n_boot=200)
    np.testing.assert_allclose(forward.ci_low, -reverse.ci_high, atol=1e-14)
    np.testing.assert_allclose(forward.ci_high, -reverse.ci_low, atol=1e-14)
    # Ajouter le même taux variable aux rendements et au sans-risque ne change rien.
    shifted = paired_sharpe_bootstrap(a + rf, b + rf, 2 * rf, n_boot=200)
    np.testing.assert_allclose(forward.ci_low, shifted.ci_low, atol=1e-14)


def test_percentiles_against_explicit_paired_samples():
    a, b, rf = series()
    indices = np.stack([np.roll(np.arange(48), k)[:24].repeat(2) for k in range(100)])
    # Oracle scalaire indépendant : calcul de chaque Sharpe via les séries pandas.
    values = []
    for idx in indices:
        ea, eb = (a - rf).iloc[idx], (b - rf).iloc[idx]
        values.append(np.sqrt(12) * (ea.mean() / ea.std(ddof=1) - eb.mean() / eb.std(ddof=1)))
    with patch("efficient_frontier.inference.circular_indices", return_value=indices):
        result = paired_sharpe_bootstrap(a, b, rf, block_lengths=(6,), n_boot=100).iloc[0]
    low, high = np.quantile(values, [0.025, 0.975])
    assert result.ci_low == pytest.approx(low, abs=1e-14)
    assert result.ci_high == pytest.approx(high, abs=1e-14)


def test_seed_is_reproducible_and_block_order_independent():
    a, b, rf = series()
    first = paired_sharpe_bootstrap(a, b, rf, n_boot=200)
    second = paired_sharpe_bootstrap(a, b, rf, block_lengths=(12, 3, 6), n_boot=200)
    pd.testing.assert_frame_equal(first, second.sort_values("block_months").reset_index(drop=True))


@pytest.mark.parametrize("bad", ["shift", "gap", "nan", "constant", "duplicate"])
def test_bad_inputs_fail_explicitly(bad):
    a, b, rf = series()
    if bad == "shift":
        b.index = b.index + pd.offsets.MonthEnd(1)
    elif bad == "gap":
        a, b, rf = (s.drop(s.index[3]) for s in (a, b, rf))
    elif bad == "nan":
        a.iloc[2] = np.nan
    elif bad == "constant":
        a = rf.copy()
    elif bad == "duplicate":
        a.index = a.index.where(a.index != a.index[1], a.index[0])
    with pytest.raises(ValueError):
        paired_sharpe_bootstrap(a, b, rf, n_boot=100)


@pytest.mark.parametrize("kwargs", [{"n_boot": 0}, {"block_lengths": (25,)}, {"block_lengths": (0,)},
                                    {"block_lengths": (6, 6)}, {"confidence": 1.0}])
def test_bad_parameters_fail(kwargs):
    with pytest.raises(ValueError):
        paired_sharpe_bootstrap(*series(), **kwargs)
