import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from aa.validation.matlab_parity import compare_metrics, parity_ok


def test_compare_metrics_and_parity_ok():
    ref = {
        "a": {"mean_ew": 0.02, "t_stat_ew": 1.0},
        "b": {"mean_ew": 0.03, "t_stat_ew": 1.5},
    }
    cand_within = {
        "a": {"mean_ew": 0.021, "t_stat_ew": 0.995},
        # difference from reference is 0.01 for both metrics
        "b": {"mean_ew": 0.031, "t_stat_ew": 1.49},
    }
    diff_df, flag_df = compare_metrics(ref, cand_within, tolerance=0.02)
    # All differences should be within tolerance
    assert flag_df["within_tolerance"].all()
    assert parity_ok(ref, cand_within, tolerance=0.02)
    # Introduce a large discrepancy
    cand_bad = {
        "a": {"mean_ew": 0.5, "t_stat_ew": 0.995},
        "b": {"mean_ew": 0.031, "t_stat_ew": 1.48},
    }
    _, flag_df2 = compare_metrics(ref, cand_bad, tolerance=0.1)
    # At least one metric should exceed tolerance
    assert not flag_df2["within_tolerance"].all()
    assert not parity_ok(ref, cand_bad, tolerance=0.1)
