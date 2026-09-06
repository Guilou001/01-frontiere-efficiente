# Commandes courantes. Prérequis : uv (https://docs.astral.sh/uv/).
UV ?= uv

.PHONY: setup data run run-us run-canada inference demo test lint clean

setup:        ## environnement épinglé (.venv) depuis uv.lock, Python 3.12
	$(UV) sync --locked --all-extras

data:         ## télécharge prix (yfinance) et taux sans risque (FRED, Banque du Canada) dans data/raw/
	$(UV) run python scripts/fetch_data.py

run: run-us run-canada   ## pipeline complet sur les deux univers (environ 3 minutes)
	$(UV) run python scripts/sharpe_uncertainty.py

inference:    ## incertitude de l'écart de Sharpe depuis les rendements publiés, sans réseau
	$(UV) run python scripts/sharpe_uncertainty.py

run-us:
	$(UV) run efficient-frontier run --universe us --n-sim 50000 --seed 123 --estimator sample
	$(UV) run efficient-frontier run --universe us --n-sim 50000 --seed 123 --estimator ledoit_wolf

run-canada:
	$(UV) run efficient-frontier run --universe canada --n-sim 50000 --seed 123 --estimator sample
	$(UV) run efficient-frontier run --universe canada --n-sim 50000 --seed 123 --estimator ledoit_wolf

demo:         ## pipeline sur données synthétiques, sans réseau (sorties dans results/demo/)
	$(UV) run efficient-frontier demo

test:         ## tests unitaires (aucune donnée externe)
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests scripts

clean:
	rm -rf results/demo .pytest_cache .ruff_cache

.PHONY: report
report:       ## PDF depuis le README, mêmes résultats et figures
	$(UV) run --extra rapport gvf rapport .
