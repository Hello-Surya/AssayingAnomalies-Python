"""
Top‑level package for the Assaying Anomalies Python port.

This package mirrors the structure of the original MATLAB library
(`AssayingAnomalies`) but provides a fully Pythonic API built on
``pandas``.  Subpackages expose functions for constructing
characteristics, forming portfolios, running cross‑sectional
regressions and producing formatted tables.  All functions are
stateless and operate on tidy data structures.

Importing the top‑level package re‑exports the major subpackages:

* :mod:`aa.asset_pricing` – univariate/double sorts and
  Fama–MacBeth regressions.
* :mod:`aa.analysis` – performance metrics, large‑scale anomaly
  evaluation and ranking utilities.
* :mod:`aa.reporting` – helper functions to convert results into
  Markdown and LaTeX tables.

New in milestone 7 is the :mod:`aa.analysis.anomaly_pipeline`
which provides a convenient interface for evaluating many anomaly
signals simultaneously.  See the documentation of that module for
details.
"""

from . import asset_pricing, analysis, reporting, validation  # noqa: F401

__all__ = [
    "asset_pricing",
    "analysis",
    "reporting",
    "validation",
]
