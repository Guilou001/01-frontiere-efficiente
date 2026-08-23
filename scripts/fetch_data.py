"""Télécharge les données brutes dans data/raw/ (idempotent, relancer avec --force pour rafraîchir).

* Prix de clôture ajustés quotidiens (yfinance, auto_adjust=True) des deux univers de FNB définis dans
  ``efficient_frontier.config`` -> ``prices_us.parquet`` et ``prices_canada.parquet`` ;
* taux sans risque : bons du Trésor américain 3 mois (FRED TB3MS, CSV sans clé) et bons du Trésor canadien
  3 mois (Banque du Canada, série TB.CDN.90D.MID, CSV sans clé) ;
* ``manifest.json`` : date de téléchargement, source, tickers, bornes, nombre de lignes, sha256 de chaque fichier.

Les fichiers de prix ne sont pas versionnés (conditions d'utilisation de Yahoo Finance).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from efficient_frontier.config import DATA_RAW, END, RF_SOURCES, UNIVERSES  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_prices(name: str, force: bool) -> dict:
    import yfinance as yf

    u = UNIVERSES[name]
    out = DATA_RAW / u.prices_file
    if out.exists() and not force:
        print(f"déjà présent : {out.name}")
    else:
        data = yf.download(list(u.tickers), start=u.price_start, end=END, interval="1d", auto_adjust=True,
                           group_by="ticker", threads=True, progress=False)
        frame = pd.DataFrame({t: data[t]["Close"] for t in u.tickers})
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        frame.index.name = "Date"
        frame = frame.dropna(how="all")
        frame.to_parquet(out)
        print(f"écrit : {out.name} {frame.shape}")
    frame = pd.read_parquet(out)
    first_valid = {t: str(frame[t].first_valid_index().date()) for t in frame.columns}
    return {
        "source": "Yahoo Finance via yfinance (auto_adjust=True, Close)",
        "tickers": list(u.tickers),
        "requested_start": u.price_start,
        "requested_end": END,
        "first_valid_date": first_valid,
        "last_date": str(frame.index.max().date()),
        "rows": int(len(frame)),
        "sha256": sha256(out),
    }


def fetch_rf(fname: str, force: bool) -> dict:
    out = DATA_RAW / fname
    url = RF_SOURCES[fname]
    if out.exists() and not force:
        print(f"déjà présent : {out.name}")
    else:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        out.write_text(resp.text, encoding="utf-8")
        print(f"écrit : {out.name} ({len(resp.text)} octets)")
    return {"source": url, "bytes": out.stat().st_size, "sha256": sha256(out)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true", help="retélécharger même si le fichier existe")
    args = parser.parse_args()
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = DATA_RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for name, u in UNIVERSES.items():
        info = fetch_prices(name, args.force)
        manifest[u.prices_file] = {"downloaded_at": stamp, **info}
    for fname in RF_SOURCES:
        manifest[fname] = {"downloaded_at": stamp, **fetch_rf(fname, args.force)}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"manifeste : {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
