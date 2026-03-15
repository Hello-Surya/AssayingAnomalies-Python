"""Pytest configuration for the Assaying Anomalies tests.

This file modifies ``sys.path`` so that the ``aa`` package in the
project root is importable when running tests from within the
repository.  Without this configuration, Python may not locate the
package because the root directory is not on ``sys.path`` by default.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
