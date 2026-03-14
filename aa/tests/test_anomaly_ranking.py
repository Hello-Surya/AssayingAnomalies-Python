import os
import sys
import numpy as np
import pandas as pd

# Make the package importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from aa.analysis.anomaly_ranking import rank_anomalies, top_decile, average_rank


def test_rank_anomalies_and_top_decile():
    metrics = {
        "a": {"mean_ew": 0.02},
        "b": {"mean_ew": 0.05},
        "c": {"mean_ew": -0.01},
        "d": {"mean_ew": 0.05},
    }
    ranks = rank_anomalies(metrics, metric="mean_ew", ascending=False)
    # b and d should tie for rank 1, a rank 3, c rank 4
    assert ranks.loc["b", "rank"] == 1.0
    assert ranks.loc["d", "rank"] == 1.0
    assert ranks.loc["a", "rank"] == 3.0
    assert ranks.loc["c", "rank"] == 4.0
    # Top decile (10% of 4 anomalies -> 1) should return one row
    top = top_decile(ranks)
    assert len(top) == 1
    # The top anomaly should be either b or d
    assert top.index[0] in {"b", "d"}


def test_average_rank():
    metrics = {
        "x": {"mean_ew": 0.05, "t_stat_ew": 2.0},
        "y": {"mean_ew": 0.02, "t_stat_ew": 3.0},
        "z": {"mean_ew": 0.01, "t_stat_ew": 1.0},
    }
    avg = average_rank(metrics, ["mean_ew", "t_stat_ew"])
    # z should have the worst average rank
    assert avg.loc["z", "avg_rank"] > avg.loc["x", "avg_rank"]
    assert avg.loc["z", "avg_rank"] > avg.loc["y", "avg_rank"]
    # x and y should tie for best average rank (1.5)
    assert abs(avg.loc["x", "avg_rank"] - avg.loc["y", "avg_rank"]) < 1e-12
