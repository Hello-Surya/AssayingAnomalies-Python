import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from aa.reporting.library_tables import performance_tables, ranking_tables
from aa.analysis.anomaly_ranking import rank_anomalies


def test_performance_and_ranking_tables():
    metrics = {
        "a": {"mean_ew": 0.02, "t_stat_ew": 1.0},
        "b": {"mean_ew": 0.03, "t_stat_ew": 1.5},
    }
    # Performance table in DataFrame format
    perf_df = performance_tables(metrics, to="dataframe")
    assert isinstance(perf_df, pd.DataFrame)
    # Should have shape (2, 2) and column names matching metrics keys
    assert perf_df.shape == (2, 2)
    assert list(perf_df.columns) == list(metrics["a"].keys())
    # Ranking table
    ranks = rank_anomalies(metrics, metric="mean_ew")
    rank_df = ranking_tables(ranks, to="dataframe")
    assert isinstance(rank_df, pd.DataFrame)
    assert "rank" in rank_df.columns
    # Check that ranking order matches expectation
    assert rank_df.index[0] == "b"
