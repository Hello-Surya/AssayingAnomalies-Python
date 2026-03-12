"""Utility functions and helpers for the aa package.

This package aggregates a handful of helpers used by various
components of the Assaying Anomalies Python port.  Functions are
explicitly imported here to provide a clean public API.  Refer to
individual submodules for detailed documentation.
"""

from .ids import normalize_permno, keep_common_equity
from .statistics import winsorize, rank_series, lag

__all__ = [
    "normalize_permno",
    "keep_common_equity",
    "winsorize",
    "rank_series",
    "lag",
]
