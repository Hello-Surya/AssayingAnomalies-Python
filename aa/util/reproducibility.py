"""
aa.util.reproducibility
=======================

Helpers for deterministic and reproducible execution of the
Assaying Anomalies pipeline.
"""

from __future__ import annotations

import datetime
import hashlib
import importlib
import json
import platform
import random
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

_TORCH: Any
try:
    _TORCH = importlib.import_module("torch")
except ImportError:
    _TORCH = None


def set_random_seed(seed: int = 0) -> None:
    """Seed global random number generators for reproducible results."""
    random.seed(seed)
    np.random.seed(seed)
    if _TORCH is not None:
        _TORCH.manual_seed(seed)
        if _TORCH.cuda.is_available():
            _TORCH.cuda.manual_seed_all(seed)
        _TORCH.backends.cudnn.deterministic = True
        _TORCH.backends.cudnn.benchmark = False


def get_experiment_hash(config: dict[str, Any]) -> str:
    """Return a SHA-256 hash of a configuration dictionary."""
    serialized = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def get_reproducibility_metadata(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Gather reproducibility metadata for the current session."""
    metadata: dict[str, Any] = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
    }
    if config is not None:
        metadata["config_hash"] = get_experiment_hash(config)
    return metadata


def log_reproducibility_metadata(path: str | Path, metadata: dict[str, Any]) -> None:
    """Write reproducibility metadata to a JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


# Additional reproducibility helpers
def get_experiment_id(config: Dict[str, Any]) -> str:
    """
    Derive a short identifier for an experiment from its configuration.

    The experiment ID is the first eight characters of the SHA-256 hash of
    the configuration.  It can be used to group related outputs and
    simplify log filenames.

    Parameters
    ----------
    config : dict
        Experiment configuration dictionary.

    Returns
    -------
    str
        Eight-character hexadecimal experiment identifier.
    """
    full_hash = get_experiment_hash(config)
    return full_hash[:8]


def create_reproducibility_log(
    config: Dict[str, Any],
    experiment_name: str,
) -> Dict[str, Any]:
    """
    Assemble a reproducibility log for an experiment.

    This convenience function combines the standard reproducibility metadata,
    the experiment name and a derived experiment ID into a single mapping.

    Parameters
    ----------
    config : dict
        Experiment configuration used to generate the outputs.
    experiment_name : str
        Human-readable name identifying the experiment.

    Returns
    -------
    dict
        Combined reproducibility metadata suitable for logging.
    """
    metadata = get_reproducibility_metadata(config)
    metadata["experiment_name"] = experiment_name
    metadata["experiment_id"] = get_experiment_id(config)
    return metadata


__all__ = [
    "set_random_seed",
    "get_experiment_hash",
    "get_reproducibility_metadata",
    "log_reproducibility_metadata",
    "get_experiment_id",
    "create_reproducibility_log",
]
