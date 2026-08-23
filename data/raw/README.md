# data/raw (non versionné)

Fichiers écrits par `scripts/fetch_data.py` (`make data`) :

| Fichier | Contenu | Source |
|---|---|---|
| `prices_us.parquet` | clôtures ajustées quotidiennes des 11 FNB américains, 2007-11 -> 2026-07 | Yahoo Finance via yfinance |
| `prices_canada.parquet` | clôtures ajustées quotidiennes des 11 FNB canadiens, 2010-11 -> 2026-07 | Yahoo Finance via yfinance |
| `rf_us_tb3ms.csv` | bons du Trésor américain 3 mois, mensuel, % annualisé | FRED, série TB3MS |
| `rf_canada_tb90.csv` | bons du Trésor canadien 3 mois, quotidien, % annualisé | Banque du Canada, Valet, TB.CDN.90D.MID |
| `manifest.json` | date de téléchargement, bornes, tickers, sha256 | écrit par le script |

Les prix ne sont pas redistribués (conditions d'utilisation de Yahoo Finance) ; les séries FRED et Banque du
Canada sont publiques et citées dans le README.
