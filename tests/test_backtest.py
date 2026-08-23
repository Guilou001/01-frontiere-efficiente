"""Backtest glissant : bornes de rotation, coûts, métriques, métriques sur séries connues."""

import numpy as np
import pandas as pd

from efficient_frontier.backtest import STRATEGIES, metrics_table, performance_metrics, walk_forward


def test_walk_forward_turnover_is_between_zero_and_two(synthetic):
    returns, rf = synthetic
    bt = walk_forward(returns.iloc[:120], rf.iloc[:120], window=60, estimator="sample", cost_bps=10.0)
    assert set(bt.turnover.columns) == set(STRATEGIES)
    assert (bt.turnover >= 0).all().all() and (bt.turnover <= 2).all().all()
    assert len(bt.returns_net) == 60
    # l'équipondéré a une rotation faible (dérive seulement) après le premier mois
    assert bt.turnover["equal_weight"].iloc[1:].max() < 0.2
    for s in STRATEGIES:
        w = bt.weights[s].to_numpy()
        np.testing.assert_allclose(w.sum(axis=1), 1.0, atol=1e-8)
        assert (w >= 0).all()


def test_costs_reduce_net_returns(synthetic):
    returns, rf = synthetic
    bt = walk_forward(returns.iloc[:100], rf.iloc[:100], window=60, cost_bps=10.0)
    assert (bt.returns_net <= bt.returns_gross + 1e-12).all().all()
    bt0 = walk_forward(returns.iloc[:100], rf.iloc[:100], window=60, cost_bps=0.0)
    pd.testing.assert_frame_equal(bt0.returns_net, bt0.returns_gross)


def test_performance_metrics_on_constant_return():
    idx = pd.date_range("2010-01-31", periods=120, freq="ME")
    r = pd.Series(0.01, index=idx)
    rf = pd.Series(0.0, index=idx)
    m = performance_metrics(r, rf, pd.Series(0.1, index=idx))
    assert abs(m["cagr"] - (1.01**12 - 1)) < 2e-3  # années civiles contre 12 mois exacts
    assert m["max_drawdown"] == 0.0
    assert abs(m["turnover_annual"] - 1.2) < 1e-12
    assert m["n_months"] == 120


def test_metrics_table_marks_estimator_free_rules(synthetic):
    returns, rf = synthetic
    bt = walk_forward(returns.iloc[:90], rf.iloc[:90], window=60, estimator="ledoit_wolf")
    tbl = metrics_table(bt).set_index("strategy")
    assert tbl.loc["equal_weight", "estimator"] == "aucun"
    assert tbl.loc["max_sharpe", "estimator"] == "ledoit_wolf"
    assert {"cagr", "vol", "sharpe", "max_drawdown", "turnover_annual"} <= set(tbl.columns)
