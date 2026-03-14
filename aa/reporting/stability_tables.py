"""
Stability and robustness reporting utilities.

This module provides placeholder functions for stability and
robustness tables.  The full implementations were introduced in
earlier milestones and are beyond the scope of milestone 7.  The
functions defined here exist solely to preserve API compatibility
with the original package and raise ``NotImplementedError`` when
called.
"""

from __future__ import annotations

from typing import Any, Dict

__all__ = ["stability_table", "robustness_table", "null_distribution_summary"]


def stability_table(*args: Any, **kwargs: Any) -> Dict[str, str]:  # pragma: no cover
    """Placeholder for the stability table function.

    Raises
    ------
    NotImplementedError
        Always raised.  The full stability reporting utilities were
        introduced in milestone 4 and are not ported here.
    """
    raise NotImplementedError(
        "stability_table is not implemented in this simplified port."
    )


def robustness_table(*args: Any, **kwargs: Any) -> Dict[str, str]:  # pragma: no cover
    """Placeholder for the robustness table function.

    Raises
    ------
    NotImplementedError
        Always raised.  The full robustness reporting utilities were
        introduced in milestone 4 and are not ported here.
    """
    raise NotImplementedError(
        "robustness_table is not implemented in this simplified port."
    )


def null_distribution_summary(
    *args: Any, **kwargs: Any
) -> Dict[str, str]:  # pragma: no cover
    """Placeholder for null distribution summary function.

    Raises
    ------
    NotImplementedError
        Always raised.  The null distribution summary was introduced
        in milestone 4 and is not ported here.
    """
    raise NotImplementedError(
        "null_distribution_summary is not implemented in this simplified port."
    )
