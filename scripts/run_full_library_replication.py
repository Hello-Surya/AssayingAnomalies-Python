#!/usr/bin/env python3
"""
Run the full Assaying Anomalies library replication pipeline.

This script wraps :func:`aa.pipeline.run_anomaly_library` to evaluate
multiple anomaly signals on a dataset and then generates a suite of
publication‑style tables and figures using the helpers in
``aa.reporting.paper_tables`` and ``aa.vis.paper_figures``.  It
optionally writes the outputs to disk via ``aa.reporting.export_utils``.

Usage
-----
```
python scripts/run_full_library_replication.py --input my_panel.csv \
    --signals size value momentum --returns ret --size me --bins 5 \
    --metric mean_ew --output outputs/
```

The output directory will contain CSV files for each table and PNG
images for each figure.  Markdown and LaTeX outputs can also be
requested via the ``--format`` flag.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional


from aa.pipeline.run_anomaly_library import run_anomaly_library
from aa.reporting.paper_tables import (
    performance_summary,
    long_short_stats,
    ranking_table,
    t_statistics_table,
    sharpe_ratio_table,
)
from aa.vis.paper_figures import (
    plot_cumulative_returns,
    plot_performance_comparison,
    plot_return_distribution,
    plot_portfolio_spreads,
)
from aa.reporting.export_utils import export_tables, export_figure


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run full library replication and produce tables/figures"
    )
    parser.add_argument(
        "--input", required=True, help="Path to panel CSV or Parquet file"
    )
    parser.add_argument(
        "--signals", nargs="*", default=None, help="List of signal columns to evaluate"
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
        "--metric", default="mean_ew", help="Metric used for ranking anomalies"
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Rank anomalies in ascending order (smaller is better)",
    )
    parser.add_argument(
        "--output", default=None, help="Directory to save output tables and figures"
    )
    parser.add_argument(
        "--format",
        default="csv",
        choices=["csv", "markdown", "latex"],
        help="Output format for tables",
    )
    parser.add_argument(
        "--value_weighted",
        action="store_true",
        help="Use value‑weighted high–low series for long–short statistics and figures",
    )
    args = parser.parse_args(argv)

    # Run the evaluation and ranking pipeline
    report = run_anomaly_library(
        args.input,
        signals=args.signals,
        returns_col=args.returns,
        size_col=args.size,
        exch_col=args.exch,
        bins=args.bins,
        ranking_metric=args.metric,
        ranking_ascending=args.ascending,
    )
    results = report["results"]
    metrics = report["metrics"]

    # Build paper‑style tables
    perf_df = performance_summary(metrics, average=True)
    ls_df = long_short_stats(results, value_weighted=args.value_weighted)
    rank_df = ranking_table(metrics, metric=args.metric, ascending=args.ascending)
    t_df = t_statistics_table(metrics)
    sr_df = sharpe_ratio_table(metrics)

    # Build figures
    fig_cum = plot_cumulative_returns(
        results, value_weighted=args.value_weighted, title=None
    )
    fig_cmp = plot_performance_comparison(metrics, metric=args.metric, title=None)
    fig_dist = plot_return_distribution(
        results, value_weighted=args.value_weighted, title=None
    )
    fig_spreads = plot_portfolio_spreads(
        results, value_weighted=args.value_weighted, title=None
    )

    # Save outputs if an output directory is provided
    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Export tables
        tables = {
            "performance_summary": perf_df,
            "long_short_stats": ls_df,
            "ranking_table": rank_df,
            "t_statistics": t_df,
            "sharpe_ratios": sr_df,
        }
        export_tables(tables, str(out_dir), format=args.format, index=True)
        # Export figures (always PNG regardless of table format)
        export_figure(fig_cum, str(out_dir / "cumulative_returns.png"))
        export_figure(fig_cmp, str(out_dir / "performance_comparison.png"))
        export_figure(fig_dist, str(out_dir / "return_distribution.png"))
        export_figure(fig_spreads, str(out_dir / "portfolio_spreads.png"))
    else:
        # Otherwise just print basic summaries to stdout
        print("Performance summary:\n", perf_df)
        print("\nLong–short statistics:\n", ls_df)
        print("\nRanking table:\n", rank_df)
        print("\nT‑statistics:\n", t_df)
        print("\nSharpe ratios:\n", sr_df)


if __name__ == "__main__":
    main()
