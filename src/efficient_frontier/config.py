"""Chemins du dépôt et définition des deux univers de FNB.

Les tickers retenus ont un historique complet sur la période indiquée (vérifié sur Yahoo Finance le
2026-08-23) ; les candidats écartés pour historique trop court sont listés dans ``DROPPED``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
ASSETS = ROOT / "assets"
STYLE_FILE = ASSETS / "style.mplstyle"

END = "2026-08-01"  # exclusif : le dernier mois complet est juillet 2026


@dataclass(frozen=True)
class Universe:
    name: str
    label: str
    currency: str
    tickers: tuple[str, ...]
    descriptions: dict[str, str]
    price_start: str  # premier jour de prix téléchargé (un mois avant le premier rendement)
    first_month: str  # premier rendement mensuel conservé
    rf_file: str
    rf_label: str
    dropped: dict[str, str] = field(default_factory=dict)

    @property
    def prices_file(self) -> str:
        return f"prices_{self.name}.parquet"


UNIVERSES: dict[str, Universe] = {
    "us": Universe(
        name="us",
        label="FNB américains multi-actifs (USD)",
        currency="USD",
        tickers=("SPY", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "HYG", "GLD", "DBC", "VNQ"),
        descriptions={
            "SPY": "S&P 500",
            "IWM": "Russell 2000",
            "EFA": "MSCI EAFE",
            "EEM": "MSCI marchés émergents",
            "TLT": "Trésor américain 20 ans et plus",
            "IEF": "Trésor américain 7-10 ans",
            "LQD": "obligations corporatives investment grade",
            "HYG": "obligations à haut rendement",
            "GLD": "or physique",
            "DBC": "panier de matières premières",
            "VNQ": "FPI américaines",
        },
        price_start="2007-11-01",
        first_month="2008-01",
        rf_file="rf_us_tb3ms.csv",
        rf_label="Bons du Trésor américain 3 mois (FRED TB3MS)",
    ),
    "canada": Universe(
        name="canada",
        label="FNB canadiens multi-actifs (CAD)",
        currency="CAD",
        tickers=("XIU.TO", "XSP.TO", "XIN.TO", "XEM.TO", "XBB.TO", "XCB.TO", "XRB.TO", "XHY.TO", "ZRE.TO", "CGL.TO", "XEG.TO"),
        descriptions={
            "XIU.TO": "S&P/TSX 60",
            "XSP.TO": "S&P 500 couvert en CAD",
            "XIN.TO": "MSCI EAFE couvert en CAD",
            "XEM.TO": "MSCI marchés émergents",
            "XBB.TO": "obligations canadiennes univers",
            "XCB.TO": "obligations corporatives canadiennes",
            "XRB.TO": "obligations à rendement réel",
            "XHY.TO": "haut rendement américain couvert en CAD",
            "ZRE.TO": "FPI canadiennes équipondérées",
            "CGL.TO": "or physique couvert en CAD",
            "XEG.TO": "énergie canadienne (S&P/TSX plafonné)",
        },
        price_start="2010-11-01",
        first_month="2011-01",
        rf_file="rf_canada_tb90.csv",
        rf_label="Bons du Trésor canadien 3 mois (Banque du Canada TB.CDN.90D.MID)",
        dropped={
            "XEF.TO": "premier prix Yahoo le 2013-04-15, remplacé par XIN.TO (2002)",
            "XBM.TO": "premier prix Yahoo le 2012-01-24, écarté (XEG.TO retenu comme secteur canadien)",
        },
    ),
}

RF_SOURCES = {
    "rf_us_tb3ms.csv": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TB3MS",
    "rf_canada_tb90.csv": "https://www.bankofcanada.ca/valet/observations/TB.CDN.90D.MID/csv?start_date=2001-01-01",
}
