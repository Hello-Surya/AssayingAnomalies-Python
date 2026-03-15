"""
Unit tests for the paper‑style reporting functions.

These tests verify that the tables produced by
``aa.reporting.paper_tables`` have the correct structure and that
ranking and long–short statistics behave as expected on synthetic
data.  The tests are based on simple, contrived inputs to avoid
dependencies on the full Assaying Anomalies pipeline.
"""

from __future__ import annotations

import math
import unittest
import pandas as pd

from aa.reporting.paper_tables import (
    performance_summary,
    long_short_stats,
    ranking_table,
    t_statistics_table,
    sharpe_ratio_table,
)


class TestPaperTables(unittest.TestCase):
    """Tests for the functions defined in paper_tables.py."""

    def setUp(self) -> None:
        # Synthetic metrics for two anomalies
        self.metrics = {
            "anomaly1": {
                "mean_ew": 0.01,
                "mean_vw": 0.02,
                "t_stat_ew": 2.5,
                "t_stat_vw": 3.0,
                "sharpe_ew": 0.5,
                "sharpe_vw": 0.6,
                "max_dd_ew": -0.1,
                "max_dd_vw": -0.2,
            },
            "anomaly2": {
                "mean_ew": 0.03,
                "mean_vw": 0.04,
                "t_stat_ew": 1.0,
                "t_stat_vw": 1.5,
                "sharpe_ew": 0.7,
                "sharpe_vw": 0.8,
                "max_dd_ew": -0.15,
                "max_dd_vw": -0.25,
            },
        }
        # Synthetic high‑minus‑low time series for two anomalies
        idx = pd.date_range("2020-01-01", periods=5, freq="M")
        self.results = {
            "anomaly1": {
                "hl_ts": pd.DataFrame(
                    {
                        "hl_ew": [0.01, 0.02, -0.01, 0.00, 0.03],
                        "hl_vw": [0.02, 0.01, -0.02, 0.01, 0.04],
                    },
                    index=idx,
                ),
            },
            "anomaly2": {
                "hl_ts": pd.DataFrame(
                    {
                        "hl_ew": [0.03, -0.01, 0.02, 0.00, 0.01],
                        "hl_vw": [0.04, -0.02, 0.03, 0.01, 0.02],
                    },
                    index=idx,
                ),
            },
        }

    def test_performance_summary(self) -> None:
        # Basic summary should include all metrics
        df = performance_summary(self.metrics, average=True)
        # Two anomalies plus one average row
        self.assertEqual(df.shape[0], 3)
        # Check that average row is last and labelled 'Average'
        self.assertEqual(df.index[-1], "Average")
        # Check that the mean_ew average is the average of the anomalies
        expected_mean_ew = (0.01 + 0.03) / 2
        self.assertAlmostEqual(df.loc["Average", "mean_ew"], expected_mean_ew)
        # Restrict to a subset of columns
        subset = performance_summary(self.metrics, include=["mean_ew", "sharpe_ew"])
        self.assertListEqual(list(subset.columns), ["mean_ew", "sharpe_ew"])

    def test_long_short_stats(self) -> None:
        # Equal‑weighted stats
        stats_ew = long_short_stats(self.results, value_weighted=False)
        self.assertListEqual(
            sorted(stats_ew.columns.tolist()), ["max_dd", "mean", "sharpe", "t_stat"]
        )
        # Check mean for anomaly1 equal‑weighted
        series = self.results["anomaly1"]["hl_ts"]["hl_ew"]
        # The expected mean return is simply the average of the series
        expected_mean = series.mean()
        self.assertAlmostEqual(stats_ew.loc["anomaly1", "mean"], expected_mean)
        # Value‑weighted stats
        stats_vw = long_short_stats(self.results, value_weighted=True)
        self.assertIn("anomaly2", stats_vw.index)
        # t‑statistic should be (mean / (std / sqrt(n)))
        series_vw = self.results["anomaly2"]["hl_ts"]["hl_vw"]
        n = len(series_vw)
        mean_vw = series_vw.mean()
        std_vw = series_vw.std(ddof=1)
        expected_t = mean_vw / (std_vw / math.sqrt(n))
        self.assertAlmostEqual(stats_vw.loc["anomaly2", "t_stat"], expected_t)

    def test_ranking_table(self) -> None:
        # Rank by mean_ew descending
        ranks = ranking_table(self.metrics, metric="mean_ew", ascending=False)
        # anomaly2 should rank first since 0.03 > 0.01
        self.assertEqual(ranks.iloc[0].name, "anomaly2")
        self.assertEqual(ranks.iloc[0]["rank"], 1)
        # Ascending order should invert the rank
        ranks_asc = ranking_table(self.metrics, metric="mean_ew", ascending=True)
        self.assertEqual(ranks_asc.iloc[0].name, "anomaly1")

    def test_t_statistics_and_sharpe_tables(self) -> None:
        t_df = t_statistics_table(self.metrics)
        self.assertIn("t_stat_ew", t_df.columns)
        self.assertEqual(t_df.loc["anomaly1", "t_stat_ew"], 2.5)
        sr_df = sharpe_ratio_table(self.metrics)
        self.assertIn("sharpe_vw", sr_df.columns)
        self.assertEqual(sr_df.loc["anomaly2", "sharpe_vw"], 0.8)


if __name__ == "__main__":
    unittest.main()
