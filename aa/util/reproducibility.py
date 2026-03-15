"""
aa.util.reproducibility
=======================

This module defines a small set of helper functions to facilitate
deterministic and reproducible execution of the Assaying Anomalies
pipeline.  Randomness enters the pipeline primarily through bootstrap
procedures or stochastic algorithm choices; by setting the same seed
values on each run you ensure that these processes generate identical
results.

Functions
---------

``set_random_seed(seed)``
    Seed Python's built‑in random generator, NumPy and (optionally)
    PyTorch to achieve deterministic behaviour.

``get_experiment_hash(config)``
    Compute a reproducible hash of an experiment configuration dictionary.

``get_reproducibility_metadata(config=None)``
    Collect metadata about the current environment and optionally
    incorporate a hash of the configuration.

``log_reproducibility_metadata(path, metadata)``
    Persist metadata to a JSON file on disk.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import platform
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def set_random_seed(seed: int = 0) -> None:
    """Seed global random number generators for reproducible results.

    This function seeds Python's ``random`` module and NumPy.  If
    PyTorch is installed it will also seed both CPU and GPU PRNGs and
    enforce deterministic convolution algorithms.  If PyTorch is not
    available, the function does nothing beyond seeding Python and
    NumPy.

    Parameters
    ----------
    seed : int, optional
        Seed value to use (default ``0``).
    """
    random.seed(seed)
    np.random.seed(seed)
    # Attempt to seed PyTorch if available
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Ensure deterministic convolution operations
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def get_experiment_hash(config: Dict[str, Any]) -> str:
    """Return a SHA‑256 hash of a configuration dictionary.

    The configuration dictionary is serialised with ``json.dumps``
    using sorted keys to ensure deterministic ordering.  The resulting
    byte string is hashed using SHA‑256 and the hex digest is
    returned.

    Parameters
    ----------
    config : dict
        Experiment configuration parameters.

    Returns
    -------
    str
        Hexadecimal digest of the hash.
    """
    serialized = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def get_reproducibility_metadata(
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Gather reproducibility metadata for the current session.

    This includes the timestamp, Python version, operating system
    information and versions of key packages (`numpy` and `pandas`).
    If a configuration dictionary is provided, a hash of that
    configuration is also included.

    Parameters
    ----------
    config : dict, optional
        Experiment configuration parameters.  If provided, they are not
        stored directly in the metadata but are hashed via
        ``get_experiment_hash``.

    Returns
    -------
    dict
        A dictionary containing metadata fields.
    """
    metadata: Dict[str, Any] = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
    }
    if config is not None:
        metadata["config_hash"] = get_experiment_hash(config)
    return metadata


def log_reproducibility_metadata(path: str | Path, metadata: Dict[str, Any]) -> None:
    """Write reproducibility metadata to a JSON file.

    The target directory is created if it does not already exist.

    Parameters
    ----------
    path : str or Path
        File path where the metadata should be saved.
    metadata : dict
        Metadata dictionary returned by ``get_reproducibility_metadata``.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


__all__ = [
    "set_random_seed",
    "get_experiment_hash",
    "get_reproducibility_metadata",
    "log_reproducibility_metadata",
]
