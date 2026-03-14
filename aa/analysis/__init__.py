"""
Analysis subpackage for Assaying Anomalies.

This namespace collects helper functions used in empirical asset
pricing analysis.  It includes implementations of common
performance metrics (mean return, t‑statistic, Sharpe ratio,
drawdown and turnover), tools for evaluating many anomaly signals
simultaneously and routines to rank anomalies based on their
performance.

Typical usage::

    from aa.analysis import evaluate_anomaly, evaluate_signals, rank_anomalies
    metrics = evaluate_anomaly(return_series)
    results = evaluate_signals(panel, signals=["size", "value"])
    ranks = rank_anomalies(results, key="mean")

The submodules are also accessible directly under
``aa.analysis.anomaly_metrics``, ``aa.analysis.anomaly_pipeline`` and
``aa.analysis.anomaly_ranking``.
"""

from .anomaly_metrics import (
    mean_return,
    t_statistic,
    sharpe_ratio,
    max_drawdown,
    compute_turnover,
    evaluate_anomaly,
)
from .anomaly_pipeline import evaluate_signals
from .anomaly_ranking import (
    rank_anomalies,
    top_decile,
    average_rank,
)

__all__ = [
    "mean_return",
    "t_statistic",
    "sharpe_ratio",
    "max_drawdown",
    "compute_turnover",
    "evaluate_anomaly",
    "evaluate_signals",
    "rank_anomalies",
    "top_decile",
    "average_rank",
]
