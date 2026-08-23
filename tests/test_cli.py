"""La démo en ligne de commande tourne sans réseau et écrit tables et figures."""

import json

from efficient_frontier.cli import main


def test_cli_demo_writes_tables_and_figures(tmp_path):
    rc = main(["demo", "--out", str(tmp_path), "--n-sim", "2000", "--n-boot", "5", "--n-points", "12", "--n-months", "130"])
    assert rc == 0
    tables = {p.name for p in (tmp_path / "tables").iterdir()}
    assert {"frontier_sample.csv", "special_portfolios_sample.csv", "montecarlo_summary_sample.csv", "oos_metrics.csv",
            "resampled_frontier_sample.csv", "summary_sample.json"} <= tables
    figures = {p.name for p in (tmp_path / "figures").iterdir()}
    assert {"cloud_dirichlet_sample.png", "cloud_dirichlet_sample.pdf", "transition_map_sample.png", "corr_heatmap_sample.png",
            "resampled_vs_analytical_sample.png", "oos_growth.png", "oos_weights_sample.png", "cloud_interactive_sample.html"} <= figures
    summary = json.loads((tmp_path / "tables" / "summary_sample.json").read_text())
    assert summary["n_assets"] == 6 and summary["n_sim"] == 2000
