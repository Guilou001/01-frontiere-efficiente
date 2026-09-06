"""Oracles à deux actifs : annualisation, taux sans risque et contraintes."""

import numpy as np
import pandas as pd
import pytest
from finquant.type_utilities import type_dict

from efficient_frontier.finquant_bridge import compare_finquant
from efficient_frontier.frontier import Frontier


def test_finquant_matches_two_asset_closed_form():
    # Actifs indépendants, variances 0,01 et 0,04 : minimum à 80 % / 20 %.
    # Tangence : (0,06-0,02)/0,01=4 et (0,12-0,02)/0,04=2,5, puis normalisation.
    mu = pd.Series([0.06, 0.12], index=["A", "B"])
    cov = pd.DataFrame(np.diag([0.01, 0.04]), index=mu.index, columns=mu.index)
    targets = np.array([0.072, 0.084, 0.096, 0.108, 0.12])
    w_b = (targets - 0.06) / 0.06
    oracle_vol = np.sqrt(0.01 * (1 - w_b) ** 2 + 0.04 * w_b**2)
    frontier = Frontier(pd.DataFrame({"target_return": targets, "vol": oracle_vol}), list(mu.index))
    original_validator = type_dict["cov_matrix"]
    result = compare_finquant(mu, cov, 0.02, frontier)
    assert type_dict["cov_matrix"] is original_validator
    points = result.query("kind == 'frontier'")
    np.testing.assert_allclose(points["w_B"], w_b, atol=1e-6)
    np.testing.assert_allclose(points["vol"], oracle_vol, atol=1e-6)
    optimum = result.set_index("kind").loc["min_variance"]
    assert optimum["w_A"] == pytest.approx(0.8, abs=1e-3)
    tangent = result.set_index("kind").loc["tangency"]
    assert tangent["w_A"] == pytest.approx(4 / 6.5, abs=1e-3)
    # Inverser les étiquettes des colonnes de covariance ne doit pas changer le calcul.
    reordered = compare_finquant(mu, cov.loc[["B", "A"], ["B", "A"]], 0.02, frontier)
    np.testing.assert_allclose(reordered["vol"], result["vol"], atol=1e-10)


def test_finquant_rejects_infeasible_target_and_restores_validator():
    mu = pd.Series([0.06, 0.12], index=["A", "B"])
    cov = pd.DataFrame(np.diag([0.01, 0.04]), index=mu.index, columns=mu.index)
    frontier = Frontier(pd.DataFrame({"target_return": [0.5], "vol": [0.1]}), list(mu.index))
    original_validator = type_dict["cov_matrix"]
    with pytest.raises(RuntimeError, match="contraintes"):
        compare_finquant(mu, cov, 0.02, frontier)
    assert type_dict["cov_matrix"] is original_validator
