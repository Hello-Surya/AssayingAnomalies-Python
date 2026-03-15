"""Validation subpackage for the Assaying Anomalies port.

This ``__init__.py`` file exposes the functions defined in
``output_consistency.py`` at the package level for convenience.
"""

from .output_consistency import (
    check_portfolio_returns_reproducibility,
    check_anomaly_ranking_stability,
    check_fama_macbeth_consistency,
    check_summary_table_consistency,
)

__all__ = [
    "check_portfolio_returns_reproducibility",
    "check_anomaly_ranking_stability",
    "check_fama_macbeth_consistency",
    "check_summary_table_consistency",
]
