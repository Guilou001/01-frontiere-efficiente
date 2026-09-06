"""Contrôle FinQuant 0.7.0 sur les mêmes moments annualisés que le solveur QP.

Les objectifs internes de FinQuant utilisent 252 périodes. Diviser mu et Sigma
par 252, puis laisser freq=252, restitue exactement nos moments annuels.
Ce changement d'échelle ne fabrique aucune observation quotidienne.
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd
from finquant.efficient_frontier import EfficientFrontier
from finquant.type_utilities import type_dict

from .frontier import Frontier, portfolio_stats


def compare_finquant(mu: pd.Series, cov: pd.DataFrame, rf: float, frontier: Frontier) -> pd.DataFrame:
    """Recalcule chaque cible et les deux optima ; conserve les écarts et les poids.

    FinQuant ne propage pas le statut SLSQP. On vérifie donc les contraintes et les
    valeurs finies, puis publie l'écart de volatilité au solveur QP sans le masquer.
    """
    # FinQuant 0.7 compare le dtype à np.floating, comparaison devenue fausse
    # sous NumPy 2. Notre entrée est float64 ; seul ce validateur est adapté,
    # dans cette portée. Les objectifs et le solveur FinQuant restent intacts.
    cov = cov.loc[mu.index, mu.index].astype("float64")
    with patch.dict(type_dict, {"cov_matrix": ((np.ndarray, pd.DataFrame), np.float64)}):
        return _compare(mu.astype("float64"), cov, rf, frontier)


def _compare(mu: pd.Series, cov: pd.DataFrame, rf: float, frontier: Frontier) -> pd.DataFrame:
    ef = EfficientFrontier(mu / 252, cov / 252, risk_free_rate=float(rf), freq=252)
    rows = []

    def record(kind: str, w, target: float | None = None, reference_vol: float = np.nan) -> None:
        w = np.asarray(w, dtype=float).ravel()
        stat = portfolio_stats(w, mu, cov, rf)
        residual = abs(stat["ret"] - target) if target is not None else 0.0
        if not np.isfinite(w).all() or not np.isfinite(list(stat.values())).all():
            raise RuntimeError("FinQuant a produit un portefeuille non fini")
        if abs(w.sum() - 1) > 1e-6 or w.min() < -1e-7 or w.max() > 1 + 1e-7 or residual > 1e-6:
            raise RuntimeError("FinQuant ne respecte pas les contraintes du portefeuille")
        rows.append({"kind": kind, "target_return": target, **stat,
                     "vol_qp": reference_vol, "vol_gap_bp": (stat["vol"] - reference_vol) * 10_000,
                     "target_error": residual, "weight_sum_error": abs(w.sum() - 1),
                     **{f"w_{a}": float(v) for a, v in zip(mu.index, w, strict=True)}})

    for row in frontier.table.itertuples():
        record("frontier", ef.efficient_return(float(row.target_return), save_weights=False),
               float(row.target_return), float(row.vol))
    record("min_variance", ef.minimum_volatility(save_weights=False))
    # Le ratio de Sharpe maximal a le même domaine que le moteur du dépôt.
    if mu.max() > rf:
        record("tangency", ef.maximum_sharpe_ratio(save_weights=False))
    return pd.DataFrame(rows)
