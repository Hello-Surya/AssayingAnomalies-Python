"""
Experiment tracking utilities
=============================

This module defines the ``ExperimentTracker`` class used to record
metadata and configuration associated with a particular research run
of the Assaying Anomalies platform.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

__all__ = ["ExperimentTracker"]


class ExperimentTracker:
    """Record experiment metadata for reproducibility."""

    def __init__(
        self,
        *,
        base_dir: str | Path,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.config: dict[str, Any] = config or {}
        self.config_fingerprint = self._fingerprint_config(self.config)

        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        self.id = f"exp_{ts}_{self.config_fingerprint[:8]}"
        self.exp_dir = self.base_dir / self.id
        self.exp_dir.mkdir(parents=True, exist_ok=True)

        self.pipeline_info: dict[str, Any] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.env: dict[str, str | None] = self._collect_env_info()

    def _fingerprint_config(self, config: dict[str, Any]) -> str:
        """Compute a stable fingerprint for the experiment config."""
        try:
            serialized = json.dumps(config, sort_keys=True, default=str)
        except TypeError:
            serialized = json.dumps(
                {key: repr(value) for key, value in config.items()},
                sort_keys=True,
            )

        hasher = hashlib.blake2b(digest_size=16)
        hasher.update(serialized.encode("utf-8"))
        return hasher.hexdigest()

    def _collect_env_info(self) -> dict[str, str | None]:
        """Gather versions of key packages for reproducibility."""
        packages = ["numpy", "pandas", "joblib", "pyarrow"]
        versions: dict[str, str | None] = {}

        versions["python"] = (
            f"{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        )

        for pkg in packages:
            try:
                versions[pkg] = importlib.metadata.version(pkg)
            except importlib.metadata.PackageNotFoundError:
                versions[pkg] = None

        return versions

    def record_pipeline(self, *, fingerprint: str, task_order: list[str]) -> None:
        """Record pipeline structure information."""
        self.pipeline_info = {
            "fingerprint": fingerprint,
            "task_order": list(task_order),
        }

    def log_task(self, name: str, info: dict[str, Any]) -> None:
        """Append a log entry for a specific task."""
        self.tasks.setdefault(name, {}).update(info)

    def to_dict(self) -> dict[str, Any]:
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
        """Persist the experiment metadata to disk."""
        meta = self.to_dict()
        path = self.exp_dir / "experiment.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(meta, file, indent=2, default=str)
        return path
