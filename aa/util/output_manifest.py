"""
aa.util.output_manifest
=======================

Utility for recording metadata about replication experiment outputs.

This module defines functions to create a manifest describing the
results of a replication experiment. A manifest includes the experiment
name, a timestamp, the version of the ``assaying-anomalies`` package, the
configuration that produced the outputs and a mapping of descriptive
names to file paths. The manifest is saved alongside the experiment
outputs in JSON format by the replication runner.
"""

from __future__ import annotations

import datetime
from importlib.metadata import version, PackageNotFoundError
from typing import Any, Dict, Mapping, Optional


def _get_package_version(pkg_name: str = "assaying-anomalies") -> str:
    """Return the installed version of a package or 'unknown' if not found."""
    try:
        return version(pkg_name)
    except PackageNotFoundError:
        return "unknown"


def create_manifest(
    experiment_name: str,
    config: Dict[str, Any],
    outputs: Mapping[str, str],
    *,
    software_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct a manifest dictionary for a replication experiment.

    Parameters
    ----------
    experiment_name : str
        Descriptive name of the experiment (e.g. 'size_anomaly').
    config : dict
        Parsed configuration that produced the outputs.
    outputs : mapping
        Mapping from logical names (e.g. 'time_series') to file paths.
    software_version : str, optional
        Version string for the assaying-anomalies package. If omitted,
        the version is resolved dynamically.

    Returns
    -------
    dict
        Manifest dictionary containing the experiment name, timestamp,
        package version, configuration and outputs.
    """
    if software_version is None:
        software_version = _get_package_version()
    return {
        "experiment_name": experiment_name,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "package_version": software_version,
        "config": config,
        "outputs": dict(outputs),
    }


__all__ = ["create_manifest"]
