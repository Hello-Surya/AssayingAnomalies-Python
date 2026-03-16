#!/usr/bin/env python
"""
Generate a summary report for replication experiments.

This script aggregates the manifest files produced by replication experiments
and writes a human‑readable summary in Markdown format.  By default it scans
the ``replication/outputs`` directory for ``manifest.json`` files and
writes ``replication/replication_summary.md``.  See the documentation in
``docs/replication_guide.md`` for details.
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, Any


def collect_manifests(outputs_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Recursively collect manifest files under a directory.

    Parameters
    ----------
    outputs_dir : Path
        Directory containing subfolders with ``manifest.json`` files.

    Returns
    -------
    dict
        Mapping from experiment names to manifest dictionaries.
    """
    manifests: Dict[str, Dict[str, Any]] = {}
    for manifest_path in outputs_dir.rglob("manifest.json"):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        name = manifest.get("experiment_name", manifest_path.parent.name)
        manifests[name] = manifest
    return manifests


def write_summary(manifests: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """Write a Markdown summary of all experiments to a file."""
    lines = []
    lines.append("# Replication Summary\n")
    lines.append(f"Generated on {datetime.datetime.utcnow().isoformat()}Z\n")
    for name, m in sorted(manifests.items()):
        lines.append(f"## {name}\n")
        lines.append(f"- Timestamp: {m.get('timestamp')}\n")
        lines.append(f"- Package version: {m.get('package_version')}\n")
        # Outputs
        lines.append("- Outputs:\n")
        for key, path in m.get("outputs", {}).items():
            lines.append(f"  - **{key}**: {path}\n")
        # Configuration
        lines.append("- Configuration:\n")
        conf = m.get("config", {})
        for k, v in conf.items():
            lines.append(f"  - {k}: {v}\n")
        lines.append("\n")
    content = "".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    """Entry point for the summary generator."""
    parser = argparse.ArgumentParser(
        description="Generate a Markdown summary for replication experiments."
    )
    parser.add_argument(
        "--outputs_dir",
        type=str,
        default="replication/outputs",
        help="Directory containing experiment output subdirectories.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="replication/replication_summary.md",
        help="Path to the Markdown file to write the summary report.",
    )
    args = parser.parse_args()
    manifests = collect_manifests(Path(args.outputs_dir))
    write_summary(manifests, Path(args.output))


if __name__ == "__main__":
    main()
