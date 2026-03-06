"""
Experiment tracking utilities
============================
This module defines the ``ExperimentTracker`` class used to record
metadata and configuration associated with a particular research run
of the Assaying Anomalies platform.  In empirical finance, it is
crucial that every table and figure be exactly reproducible; this
requires that all parameters, random seeds, software versions and
pipeline structure be captured and logged.  The tracker stores
metadata as JSON and writes it to a directory on disk so that
experiments can be inspected later or exported for replication.

Key features
------------

* **Unique experiment IDs.**  Each experiment is assigned a stable
  identifier generated from the hash of its configuration and the
  current timestamp.  The ID is used as the directory name under
  ``base_dir``.

* **Configuration fingerprinting.**  The tracker computes a
  fingerprint of the user‑supplied configuration by serialising it
  with ``json.dumps(..., sort_keys=True)`` and hashing the result
  with Blake2b.  This ensures that experiments with identical
  configurations generate identical fingerprints.

* **Environment logging.**  The tracker records the versions of
  critical software packages (Python, NumPy, pandas, joblib, pyarrow)
  at the time of the run.  Recording software versions is a common
  recommendation for reproducible research【196710000405780†L378-L404】.

* **Pipeline and task logs.**  When a pipeline is executed the tracker
  records a fingerprint of its task structure and the order in which
  tasks were run.  Individual tasks can log arbitrary metadata (e.g.,
  whether a checkpoint was loaded or saved) via the ``log_task``
  method.  This metadata is stored in a ``tasks`` dictionary keyed
  by task name.

The ``ExperimentTracker`` maintains no global state and does not
perform any hidden I/O aside from writing its JSON file when
``save()`` is called.  Users are encouraged to call ``save`` after
running a pipeline to persist the logs; forgetting to call ``save``
will leave the tracker in memory only.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import importlib.metadata

__all__ = ["ExperimentTracker"]


class ExperimentTracker:
    """Record experiment metadata for reproducibility.

    Parameters
    ----------
    base_dir : str or Path
        Base directory in which experiment logs will be stored.  Each
        experiment creates a subdirectory named after its ``id``.
    config : dict, optional
        A dictionary of user‑defined configuration parameters.  This
        may include signal definitions, model hyperparameters or any
        other settings relevant to the run.  The configuration
        fingerprint is derived from this dictionary.

    Notes
    -----
    The ``ExperimentTracker`` does not automatically persist its
    state.  To write the metadata to disk call :meth:`save`.  The
    ``id`` attribute is computed on construction and remains stable for
    the lifetime of the instance.
    """

    def __init__(self, *, base_dir: str | Path, config: Optional[Dict[str, Any]] = None) -> None:
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.config: Dict[str, Any] = config or {}
        self.config_fingerprint = self._fingerprint_config(self.config)
        # Compose experiment ID using timestamp and config fingerprint
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        self.id = f"exp_{ts}_{self.config_fingerprint[:8]}"
        self.exp_dir = self.base_dir / self.id
        self.exp_dir.mkdir(parents=True, exist_ok=True)
        # Placeholder for pipeline and task logs
        self.pipeline_info: Dict[str, Any] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        # Collect environment info
        self.env: Dict[str, Any] = self._collect_env_info()

    # ------------------------------------------------------------------
    # Helpers
    def _fingerprint_config(self, config: Dict[str, Any]) -> str:
        # Use a stable JSON representation with sorted keys
        try:
            serialized = json.dumps(config, sort_keys=True, default=str)
        except TypeError:
            # Fallback: convert non‑serialisable objects to their repr
            serialized = json.dumps({k: repr(v) for k, v in config.items()}, sort_keys=True)
        h = hashlib.blake2b(digest_size=16)
        h.update(serialized.encode("utf-8"))
        return h.hexdigest()

    def _collect_env_info(self) -> Dict[str, Any]:
        # Gather versions of key packages for reproducibility
        packages = ["python", "numpy", "pandas", "joblib", "pyarrow"]
        versions: Dict[str, Optional[str]] = {}
        versions["python"] = f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        for pkg in packages[1:]:
            try:
                versions[pkg] = importlib.metadata.version(pkg)  # type: ignore[assignment]
            except Exception:
                versions[pkg] = None
        return versions

    # ------------------------------------------------------------------
    # Public API
    def record_pipeline(self, *, fingerprint: str, task_order: List[str]) -> None:
        """Record pipeline structure information.

        Parameters
        ----------
        fingerprint : str
            A short hash of the pipeline DAG (see
            :meth:`aa.engine.pipeline.Pipeline._fingerprint`).
        task_order : list of str
            Names of tasks in topological execution order.
        """
        self.pipeline_info = {
            "fingerprint": fingerprint,
            "task_order": list(task_order),
        }

    def log_task(self, name: str, info: Dict[str, Any]) -> None:
        """Append a log entry for a specific task.

        Parameters
        ----------
        name : str
            Task name.
        info : dict
            Arbitrary metadata about the task execution.  Information may
            include status (e.g., "loaded", "saved"), hashes, run times
            or any other details the task wants to record.
        """
        self.tasks.setdefault(name, {}).update(info)

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the experiment metadata."""
        return {
            "id": self.id,
            "config": self.config,
            "config_fingerprint": self.config_fingerprint,
            "environment": self.env,
            "pipeline": self.pipeline_info,
            "tasks": self.tasks,
        }

    def save(self) -> Path:
        """Persist the experiment metadata to disk.

        The metadata is written to ``experiment.json`` in the
        experiment directory.  If the file already exists it will be
        overwritten.  Returns the path to the written file.
        """
        meta = self.to_dict()
        path = self.exp_dir / "experiment.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
        return path
