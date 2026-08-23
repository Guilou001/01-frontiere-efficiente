"""Chargement des prix en cache (parquet), passage en rendements mensuels, taux sans risque, données synthétiques.

Aucune fonction de ce module n'accède au réseau : le téléchargement est dans ``scripts/fetch_data.py``.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_RAW, END, UNIVERSES, Universe

PERIODS_PER_YEAR = 12


def monthly_returns(prices_daily: pd.DataFrame) -> pd.DataFrame:
    """Rendements simples mensuels à partir de clôtures ajustées quotidiennes (dernier prix du mois)."""
    monthly = prices_daily.sort_index().resample("ME").last()
    return monthly.pct_change().dropna(how="any")


def load_prices(universe: Universe, data_dir: Path = DATA_RAW) -> pd.DataFrame:
    path = data_dir / universe.prices_file
    if not path.exists():
        raise FileNotFoundError(f"{path} absent : lancer `make data` (scripts/fetch_data.py) d'abord.")
    prices = pd.read_parquet(path)
    prices.index = pd.to_datetime(prices.index)
    return prices[list(universe.tickers)]


def _annual_pct_to_monthly(yields_pct: pd.Series) -> pd.Series:
    """Rendement annualisé en % (base bons du Trésor) vers taux mensuel simple."""
    return (1.0 + yields_pct / 100.0) ** (1.0 / PERIODS_PER_YEAR) - 1.0


def parse_fred_csv(text: str) -> pd.Series:
    """CSV FRED (observation_date, TB3MS) -> rendement mensuel, indexé en fin de mois."""
    frame = pd.read_csv(io.StringIO(text))
    frame.columns = ["date", "value"]
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    serie = frame.dropna().set_index(pd.to_datetime(frame.dropna()["date"]))["value"]
    serie.index = serie.index.to_period("M").to_timestamp("M")
    return _annual_pct_to_monthly(serie).rename("rf")


def parse_boc_csv(text: str) -> pd.Series:
    """CSV Valet (Banque du Canada) : en-tête libre puis bloc OBSERVATIONS quotidien -> moyenne mensuelle."""
    marker = '"OBSERVATIONS"'
    start = text.index(marker) + len(marker)
    frame = pd.read_csv(io.StringIO(text[start:].strip()))
    frame.columns = ["date", "value"]
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    serie = frame.dropna().set_index(pd.to_datetime(frame.dropna()["date"]))["value"]
    monthly_yield = serie.resample("ME").mean()
    return _annual_pct_to_monthly(monthly_yield).rename("rf")


def load_rf_monthly(universe: Universe, data_dir: Path = DATA_RAW) -> pd.Series:
    path = data_dir / universe.rf_file
    if not path.exists():
        raise FileNotFoundError(f"{path} absent : lancer `make data` d'abord.")
    text = path.read_text(encoding="utf-8-sig")
    if universe.rf_file.startswith("rf_us"):
        return parse_fred_csv(text)
    return parse_boc_csv(text)


def load_universe(name: str, data_dir: Path = DATA_RAW) -> tuple[pd.DataFrame, pd.Series, Universe]:
    """Rendements mensuels des FNB et taux sans risque mensuel, alignés sur [first_month, END)."""
    universe = UNIVERSES[name]
    returns = monthly_returns(load_prices(universe, data_dir))
    rf = load_rf_monthly(universe, data_dir)
    first = pd.Timestamp(universe.first_month + "-01")
    returns = returns.loc[(returns.index >= first) & (returns.index < pd.Timestamp(END))]
    rf = rf.reindex(returns.index).ffill()
    if rf.isna().any():
        raise ValueError("taux sans risque manquant sur une partie de la période")
    return returns, rf, universe


def synthetic_universe(n_assets: int = 6, n_months: int = 240, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    """Univers synthétique (modèle à un facteur + bruit) pour les tests et la démo sans réseau.

    Les moyennes annuelles vont de 2 % à 9 %, les volatilités de 5 % à 22 %, la corrélation au facteur
    croît avec le risque : la frontière a une forme réaliste et l'actif le moins risqué n'est pas celui
    qui rapporte le moins, ce qui évite un cas dégénéré.
    """
    rng = np.random.default_rng(seed)
    mu_annual = np.linspace(0.02, 0.09, n_assets)
    vol_annual = np.linspace(0.05, 0.22, n_assets)
    beta = np.linspace(0.2, 1.0, n_assets)
    factor = rng.standard_normal(n_months) / np.sqrt(PERIODS_PER_YEAR)
    idio = rng.standard_normal((n_months, n_assets)) / np.sqrt(PERIODS_PER_YEAR)
    shocks = vol_annual * (beta[None, :] * factor[:, None] + np.sqrt(1 - beta**2)[None, :] * idio)
    rets = mu_annual / PERIODS_PER_YEAR + shocks
    index = pd.date_range("2000-01-31", periods=n_months, freq="ME")
    cols = [f"A{i + 1}" for i in range(n_assets)]
    returns = pd.DataFrame(rets, index=index, columns=cols)
    rf = pd.Series(0.02 / PERIODS_PER_YEAR, index=index, name="rf")
    return returns, rf
