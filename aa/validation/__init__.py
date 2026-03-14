"""
Validation subpackage for Assaying Anomalies.

This namespace provides functions to compare Python outputs against
MATLAB benchmarks or other reference results.  Use these helpers
to verify that ported algorithms produce values within an
acceptable tolerance of their original counterparts.
"""

from .matlab_parity import compare_metrics, parity_ok

__all__ = ["compare_metrics", "parity_ok"]
