"""
Driver for large‑scale anomaly evaluation.

This script/function provides a high‑level entry point to run the
entire Assaying Anomalies library across a dataset of firm‑level
returns and characteristics.  It loads data, performs univariate
portfolio sorts for each signal, computes high‑minus‑low spreads,
calculates performance metrics and ranks the anomalies.  The
results can be easily exported to DataFrames, Markdown or LaTeX
tables using :mod:`aa.reporting.library_tables`.

Example (programmatic)
----------------------
>>> import pandas as pd
>>> from aa.pipeline.run_anomaly_library import run_anomaly_library
>>> panel = pd.read_csv("my_panel.csv")
>>> report = run_anomaly_library(panel, signals=["size", "value"])
>>> report["ranks"].head()

Example (command line)
----------------------
```
python -m aa.pipeline.run_anomaly_library --input my_panel.csv \
       --returns ret --size me --bins 5 --metric mean_ew
```

Notes
-----
This module assumes that the input panel DataFrame is already in
long format with columns ``date``, ``permno`` and the requisite
characteristics.  It does not perform any data cleaning beyond
dropping missing values in the sort variables.  Users are
responsible for supplying a dataset consistent with the
requirements of :func:`aa.analysis.anomaly_pipeline.evaluate_signals`.
"""

from __future__ import annotations

import argparse
from typing import Dict, List, Optional, Any, Union

import pandas as pd

from aa.analysis.anomaly_pipeline import evaluate_signals
from aa.analysis.anomaly_ranking import rank_anomalies, average_rank
from aa.reporting.library_tables import performance_tables, ranking_tables

__all__ = ["run_anomaly_library", "main"]


def run_anomaly_library(
    panel: Union[pd.DataFrame, str],
    *,
    signals: Optional[List[str]] = None,
    returns_col: str = "ret",
    size_col: str = "me",
    exch_col: str = "exchcd",
    bins: int = 5,
    nyse_breaks: bool = False,
    min_obs: int = 20,
    ranking_metric: str = "mean_ew",
    ranking_ascending: bool = False,
    metrics_for_avg_rank: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run the anomaly evaluation and ranking pipeline on a dataset.

    Parameters
    ----------
    panel : DataFrame or str
        Either a pandas DataFrame containing the panel of returns and
        characteristics or a path to a CSV/Parquet file that can be
        read into a DataFrame via :func:`pandas.read_csv` or
        :func:`pandas.read_parquet`.
    signals : list[str], optional
        List of signal columns to evaluate.  If ``None`` (default),
        all columns other than identifiers and the returns/size/exch
        columns are treated as signals.
    returns_col : str, default "ret"
        Column name for returns.
    size_col : str, default "me"
        Column name for market equity (size).  Used for
        value‑weighted returns.
    exch_col : str, default "exchcd"
        Column name for exchange codes.  Used when computing
        breakpoints with NYSE only.
    bins : int, default 5
        Number of portfolios to form in each period.
    nyse_breaks : bool, default False
        If ``True``, breakpoints are computed using NYSE stocks only.
    min_obs : int, default 20
        Minimum number of observations required per period to perform
        sorting.
    ranking_metric : str, default "mean_ew"
        Metric used to rank anomalies.  Must be present in the
        dictionary returned under ``results[sig]['metrics']``.
    ranking_ascending : bool, default False
        Whether lower metric values correspond to better ranks.
    metrics_for_avg_rank : list[str], optional
        If provided, compute the average rank across these metrics
        using :func:`aa.analysis.anomaly_ranking.average_rank`.

    Returns
    -------
    dict
        A dictionary with keys:

        ``'results'`` – The full output of
        :func:`aa.analysis.anomaly_pipeline.evaluate_signals`.

        ``'metrics'`` – A simpler dict mapping each signal to its
        metrics (extracted from ``results``).

        ``'ranks'`` – A DataFrame of ranks computed via
        :func:`aa.analysis.anomaly_ranking.rank_anomalies`.

        ``'avg_ranks'`` – A DataFrame of average ranks across
        ``metrics_for_avg_rank`` (or ``None`` if not requested).

        ``'performance_table'`` – A pandas DataFrame summarising
        metrics across anomalies (one row per anomaly, one column
        per metric).

        ``'ranking_table'`` – A pandas DataFrame containing the
        anomaly ranks.
    """
    # Load panel if path provided
    if isinstance(panel, str):
        if panel.lower().endswith(".csv") or panel.lower().endswith(".txt"):
            panel_df = pd.read_csv(panel)
        elif panel.lower().endswith(".parquet") or panel.lower().endswith(".pq"):
            panel_df = pd.read_parquet(panel)
        else:
            raise ValueError(f"Unsupported file extension for panel: {panel}")
    else:
        panel_df = panel.copy()
    # Run evaluation
    results = evaluate_signals(
        panel_df,
        signals=signals,
        returns_col=returns_col,
        size_col=size_col,
        exch_col=exch_col,
        bins=bins,
        nyse_breaks=nyse_breaks,
        min_obs=min_obs,
    )
    # Extract metrics only
    metrics_dict: Dict[str, Dict[str, Any]] = {
        sig: out["metrics"] for sig, out in results.items()
    }
    # Rank anomalies
    ranks_df = rank_anomalies(
        metrics_dict, metric=ranking_metric, ascending=ranking_ascending
    )
    avg_ranks_df: Optional[pd.DataFrame] = None
    if metrics_for_avg_rank:
        avg_ranks_df = average_rank(metrics_dict, metrics_for_avg_rank)
    # Assemble tables
    perf_table = performance_tables(metrics_dict, to="dataframe")
    rank_table = ranking_tables(ranks_df, to="dataframe")
    return {
        "results": results,
        "metrics": metrics_dict,
        "ranks": ranks_df,
        "avg_ranks": avg_ranks_df,
        "performance_table": perf_table,
        "ranking_table": rank_table,
    }


def main(argv: Optional[List[str]] = None) -> None:
    """Command‑line interface for running the anomaly library.

    Use this function as an entry point when invoking the module via
    ``python -m aa.pipeline.run_anomaly_library``.  It parses
    arguments, loads the input panel and writes Markdown tables to
    stdout.
    """
    parser = argparse.ArgumentParser(
        description="Run Assaying Anomalies library on a dataset"
    )
    parser.add_argument(
        "--input", required=True, help="Path to panel CSV or Parquet file"
    )
    parser.add_argument("--returns", default="ret", help="Name of the returns column")
    parser.add_argument(
        "--size", default="me", help="Name of the size (market equity) column"
    )
    parser.add_argument(
        "--exch", default="exchcd", help="Name of the exchange code column"
    )
    parser.add_argument(
        "--bins", type=int, default=5, help="Number of portfolios for sorting"
    )
    parser.add_argument(
        "--signals", nargs="*", default=None, help="List of signal columns to evaluate"
    )
    parser.add_argument(
        "--nyse-breaks", action="store_true", help="Use NYSE breakpoints for sorting"
    )
    parser.add_argument(
        "--min-obs", type=int, default=20, help="Minimum observations per period"
    )
    parser.add_argument(
        "--metric", default="mean_ew", help="Metric used for ranking anomalies"
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Rank metric in ascending order (default descending)",
    )
    parser.add_argument(
        "--avg-metrics", nargs="*", help="Metrics over which to average ranks"
    )
    args = parser.parse_args(argv)
    report = run_anomaly_library(
        args.input,
        signals=args.signals,
        returns_col=args.returns,
        size_col=args.size,
        exch_col=args.exch,
        bins=args.bins,
        nyse_breaks=args.nyse_breaks,
        min_obs=args.min_obs,
        ranking_metric=args.metric,
        ranking_ascending=args.ascending,
        metrics_for_avg_rank=args.avg_metrics,
    )
    # Print summary tables to stdout
    perf_df = report["performance_table"]
    rank_df = report["ranking_table"]
    if perf_df is not None and not perf_df.empty:
        print("\nPerformance Table:\n")
        print(perf_df.to_markdown())
    if rank_df is not None and not rank_df.empty:
        print("\nRanking Table:\n")
        print(rank_df.to_markdown())
    if report["avg_ranks"] is not None:
        print("\nAverage Ranks Table:\n")
        print(report["avg_ranks"].to_markdown())


if __name__ == "__main__":
    main()
