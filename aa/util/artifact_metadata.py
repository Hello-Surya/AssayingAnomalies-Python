from __future__ import annotations

import datetime
import json
import pathlib
import platform
from importlib import metadata as importlib_metadata
from typing import Any


def _safe_version(pkg: str) -> str | None:
    """Return the installed version of a package, or None if not installed."""
    try:
        return importlib_metadata.version(pkg)
    except Exception:
        return None


def gather_metadata(
    config_file: str | None = None,
    verification_report: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Collect metadata for the research artifact."""
    metadata: dict[str, Any] = {}

    try:
        import aa

        metadata["aa_version"] = getattr(aa, "__version__", "unknown")
    except Exception:
        metadata["aa_version"] = None

    metadata["python_version"] = platform.python_version()
    metadata["dependencies"] = {
        "numpy": _safe_version("numpy"),
        "pandas": _safe_version("pandas"),
        "statsmodels": _safe_version("statsmodels"),
        "matplotlib": _safe_version("matplotlib"),
        "scipy": _safe_version("scipy"),
    }

    if config_file is not None:
        config_path = pathlib.Path(config_file)
        metadata["config_file"] = str(config_path)
        try:
            import yaml

            with config_path.open("r", encoding="utf-8") as f:
                metadata["config"] = yaml.safe_load(f)
        except Exception:
            metadata["config"] = None

    if verification_report is not None:
        try:
            with verification_report.open("r", encoding="utf-8") as f:
                metadata["verification_report"] = json.load(f)
        except Exception:
            metadata["verification_report"] = None

    metadata["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()
    return metadata


def save_metadata(metadata: dict[str, Any], path: pathlib.Path) -> None:
    """Write metadata dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
