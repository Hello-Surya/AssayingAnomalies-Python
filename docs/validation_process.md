# Validation Process for Assaying Anomalies

This document describes how to verify that the Python implementation of the
**Assaying Anomalies** library produces results consistent with the
original MATLAB code.  The emphasis of this milestone is reproducibility and
determinism: given the same inputs and configuration, the pipeline should
produce identical outputs across runs and match the published MATLAB
results.  The utility modules introduced in this milestone make it
straightforward to perform these checks.

## Setting up reproducible runs

To ensure that pseudo‑random operations (for example, bootstrap sampling or
stochastic portfolio assignments) yield the same results on every run you
should fix all random seeds before invoking the pipeline.  The
`aa.util.reproducibility` module provides a convenience function for this:

```python
from aa.util.reproducibility import set_random_seed, get_reproducibility_metadata

# choose a seed value
set_random_seed(42)

# optional: capture metadata for later inspection
metadata = get_reproducibility_metadata({'seed': 42, 'signals': ['size', 'value']})
```

The `get_reproducibility_metadata` function also records information about
the Python and package versions.  You can persist this metadata alongside
your results using `log_reproducibility_metadata` to aid in future audits.

## Comparing results across runs

The `aa.validation.output_consistency` module contains a set of helper
functions for comparing outputs from two runs of the pipeline.  They are
designed to operate on pandas data structures and tolerate minor floating
point differences.  For example:

```python
from aa.validation.output_consistency import (
    check_portfolio_returns_reproducibility,
    check_anomaly_ranking_stability,
    check_fama_macbeth_consistency,
    check_summary_table_consistency,
)

# compare equal‑weighted portfolio returns
assert check_portfolio_returns_reproducibility(returns_run1, returns_run2)

# check that ranking of anomalies is identical
assert check_anomaly_ranking_stability(ranking1['anomaly'], ranking2['anomaly'])

# Fama–MacBeth coefficients and t‑statistics
assert check_fama_macbeth_consistency(fmb_results1, fmb_results2)

# summary tables (mean returns, Sharpe ratios, etc.)
assert check_summary_table_consistency(summary1, summary2)
```

Each function returns a boolean indicating whether the two inputs are
considered equal within a tolerance.  When a check fails you can manually
inspect the differences (e.g. using `pandas.testing.assert_frame_equal`) to
pinpoint discrepancies.

## Verifying parity with MATLAB outputs

To compare the Python outputs to the original MATLAB results, first run
the MATLAB scripts on a known dataset and export the outputs (tables and
figures) to CSV or a similar format.  Then run the Python pipeline on
the same dataset with identical settings.  You can load the MATLAB
outputs into pandas and compare them to the Python outputs using the
consistency functions described above.  Pay attention to the ordering of
columns and the presence of any NaNs when performing the comparison.

Because floating point arithmetic can differ slightly between platforms,
you may need to specify a tolerance when comparing numeric values.  The
default tolerances in `output_consistency.py` should be sufficient for
most cases, but you can pass a custom `tol` argument to the comparison
functions if more leniency is required.

## Translation coverage

An automated script (`scripts/check_translation_coverage.py`) can be used
to audit which MATLAB functions have been ported to Python.  It scans the
MATLAB repository for `.m` files and attempts to find snake‑case
equivalents in the Python `aa/` package.  Running this script periodically
will help ensure that no components of the original library are overlooked
during development.

For additional details on how the translation mapping was derived, see
`docs/matlab_python_mapping.md`.