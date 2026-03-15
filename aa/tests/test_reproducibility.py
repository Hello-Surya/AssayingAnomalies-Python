"""
Tests for the reproducibility utilities.

These tests ensure that setting a random seed produces deterministic
NumPy sequences and that experiment hashes are stable under key
reordering.
"""

from __future__ import annotations

import numpy as np

from aa.util.reproducibility import (
    get_experiment_hash,
    get_reproducibility_metadata,
    set_random_seed,
)


def test_set_random_seed_deterministic() -> None:
    set_random_seed(123)
    a = np.random.random(5)

    set_random_seed(123)
    b = np.random.random(5)

    assert np.allclose(a, b)


def test_get_experiment_hash_order_independence() -> None:
    config1 = {"a": 1, "b": 2}
    config2 = {"b": 2, "a": 1}

    h1 = get_experiment_hash(config1)
    h2 = get_experiment_hash(config2)

    assert h1 == h2


def test_get_reproducibility_metadata_includes_versions() -> None:
    meta = get_reproducibility_metadata()
    assert "python_version" in meta
    assert "numpy_version" in meta
    assert "pandas_version" in meta
