"""Incertitude de l'écart de Sharpe sur les rendements nets déjà réalisés.

Bootstrap circulaire apparié, intervalles percentiles non studentisés.
Les poids ne sont pas réestimés dans les tirages : l'inférence porte sur les
séries hors échantillon observées, sous stationnarité et dépendance faible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def circular_indices(n: int, block_length: int, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Blocs consécutifs avec retour au début ; dernier bloc tronqué à n mois."""
    if not all(isinstance(v, (int, np.integer)) and not isinstance(v, bool) for v in (n, block_length, n_boot)):
        raise ValueError("tailles entières requises")
    if n < 2 or not 1 <= block_length <= n or n_boot < 1:
        raise ValueError("tailles incompatibles avec le bootstrap")
    starts = rng.integers(0, n, size=(n_boot, (n + block_length - 1) // block_length))
    return ((starts[..., None] + np.arange(block_length)) % n).reshape(n_boot, -1)[:, :n]


def sharpe_difference(excess: np.ndarray, periods_per_year: int = 12) -> np.ndarray:
    """Deux séries en dernières colonnes ; axe des mois avant les colonnes."""
    excess = np.asarray(excess, dtype=float)
    if excess.ndim < 2 or excess.shape[-1] != 2 or excess.shape[-2] < 2:
        raise ValueError("deux séries et au moins deux observations requises")
    if not np.isfinite(excess).all() or not np.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("rendements finis et fréquence positive requis")
    sigma = excess.std(axis=-2, ddof=1)
    if np.any(sigma <= np.finfo(float).eps):
        raise ValueError("Sharpe indéfini : variance nulle dans une série ou un tirage")
    ratios = np.sqrt(periods_per_year) * excess.mean(axis=-2) / sigma
    return ratios[..., 0] - ratios[..., 1]


def paired_sharpe_bootstrap(
    strategy: pd.Series,
    benchmark: pd.Series,
    rf: pd.Series,
    *,
    block_lengths: tuple[int, ...] = (3, 6, 12),
    n_boot: int = 20_000,
    seed: int = 123,
    confidence: float = 0.95,
    periods_per_year: int = 12,
) -> pd.DataFrame:
    """Écart stratégie moins référence et IC appariés, sans valeur p implicite.

    Aucun mois manquant n'est retiré silencieusement. Les mêmes indices tirent
    les deux rendements et leur taux sans risque. La graine dépend de la longueur
    des blocs, pas de leur ordre d'appel. Calcul par lots pour borner la mémoire.
    """
    index = strategy.index
    if not isinstance(index, pd.DatetimeIndex) or index.hasnans or not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError("dates uniques, ordonnées et complètes requises")
    if not index.equals(benchmark.index) or not index.equals(rf.index):
        raise ValueError("les trois séries doivent avoir exactement les mêmes dates")
    if len(index) < 3 or not np.all(np.diff(index.to_period("M").asi8) == 1):
        raise ValueError("au moins trois mois consécutifs requis")
    if not 0 < confidence < 1 or not block_lengths or len(set(block_lengths)) != len(block_lengths):
        raise ValueError("niveau de confiance et longueurs de blocs invalides")
    if not isinstance(n_boot, (int, np.integer)) or isinstance(n_boot, bool) or n_boot < 100:
        raise ValueError("au moins 100 tirages entiers requis")
    raw = np.column_stack([strategy, benchmark, rf]).astype(float)
    if not np.isfinite(raw).all():
        raise ValueError("rendements finis requis, aucun mois supprimé implicitement")
    excess = raw[:, :2] - raw[:, 2, None]
    observed = float(sharpe_difference(excess, periods_per_year))
    alpha = 1 - confidence
    rows = []
    for length in block_lengths:
        if not isinstance(length, (int, np.integer)) or isinstance(length, bool) or not 1 <= length <= len(index) // 2:
            raise ValueError("blocs entiers requis, au plus la moitié de l'échantillon")
        rng = np.random.default_rng(np.random.SeedSequence([seed, int(length)]))
        draws = np.empty(n_boot)
        for start in range(0, n_boot, 500):
            stop = min(start + 500, n_boot)
            indices = circular_indices(len(index), length, stop - start, rng)
            draws[start:stop] = sharpe_difference(excess[indices], periods_per_year)
        low, high = np.quantile(draws, [alpha / 2, 1 - alpha / 2], method="linear")
        rows.append({
            "start": index[0].strftime("%Y-%m"), "end": index[-1].strftime("%Y-%m"),
            "n_months": len(index), "block_months": length, "n_boot": n_boot, "seed": seed,
            "confidence": confidence, "periods_per_year": periods_per_year,
            "method": "paired_circular_percentile", "sharpe_difference": observed,
            "ci_low": low, "ci_high": high, "bootstrap_se": draws.std(ddof=1),
            "zero_in_interval": bool(low <= 0 <= high),
        })
    return pd.DataFrame(rows)


def uncertainty_table(inputs: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Compare les deux règles de Sharpe maximal au même portefeuille équipondéré."""
    tables = []
    for estimator in ("sample", "ledoit_wolf"):
        table = paired_sharpe_bootstrap(inputs[f"max_sharpe__{estimator}"], inputs["equal_weight"], inputs["rf"], **kwargs)
        table.insert(0, "estimator", estimator)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)
