"""
Asset pricing routines (portfolio sorts, regressions).

This subpackage exposes functions for constructing portfolios and
estimating risk prices from characteristic data.  It includes

* Univariate sorts (:func:`univariate_sort`) and their configuration
  via :class:`aa.asset_pricing.univariate.SortConfig`.
* Cross‑sectional regression estimators (Fama–MacBeth) returning
  coefficients, standard errors, t‑statistics and observation counts.

Placeholder stubs are provided for double sorts and factor tests in
order to maintain API compatibility with earlier milestones.  These
functions currently raise :class:`NotImplementedError`.
"""

from .univariate import SortConfig, univariate_sort  # noqa: F401
from .fama_macbeth import fama_macbeth, fama_macbeth_full  # noqa: F401


class DoubleSortConfig:  # pragma: no cover - stub for compatibility
    """Placeholder configuration for double sorts.

    The full double sort implementation was introduced in earlier
    milestones but is not required for milestone 7.  This stub
    exists solely to satisfy imports and will be removed once the
    full module is ported.
    """

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "DoubleSortConfig is not implemented in this simplified port."
        )


def double_sort(*args, **kwargs) -> None:  # pragma: no cover - stub
    """Placeholder for the double sort function.

    The full double sort functionality is not part of milestone 7.
    Attempting to call this function will raise ``NotImplementedError``.
    """
    raise NotImplementedError("double_sort is not implemented in this simplified port.")


__all__ = [
    "SortConfig",
    "univariate_sort",
    "DoubleSortConfig",
    "double_sort",
    "fama_macbeth",
    "fama_macbeth_full",
]
