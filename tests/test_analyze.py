"""Integration tests for analyze() — the strict-mode regression we fixed.

These tests construct DataFrames in-memory rather than reading the bundled
xlsx samples, so they're fast and don't depend on the sample inputs being
present.
"""

import numpy as np
import pandas as pd
import pytest

from scorer import analyze


def _strict_frame_from_records(records, columns):
    """
    Build a DataFrame the same way load_strict() does: object dtype, with the
    pandas DataFrame constructor allowed to infer dtypes per column from the
    raw Python values. This matches what openpyxl + pd.DataFrame produce.
    """
    return pd.DataFrame(records, columns=columns)


def test_strict_mode_mixed_column_is_numeric_not_identifier():
    """
    Regression: a mostly-numeric object column (185 floats + 15 strings) used to
    be classified as 'identifier' in strict mode because is_numeric_dtype
    returned False. With the coerced numeric_view it should be 'numeric_continuous'.
    """
    rng = np.random.default_rng(42)
    values = rng.lognormal(5, 1.5, 200).round(2).tolist()
    bad_rows = set(range(0, 200, 14))  # 15 evenly-spaced rows get a sentinel string
    records = []
    for i, v in enumerate(values):
        records.append([
            float(v),
            "N/A" if i in bad_rows else float(v),
        ])
    df = _strict_frame_from_records(records, ["revenue", "revenue_mixed"])

    rankings, profiles, _, corr = analyze(df, strict_types=True)

    row = rankings[rankings["field"] == "revenue_mixed"].iloc[0]
    assert row["field_type"] == "numeric_continuous"
    assert "numeric:" in row["type_mix"]
    assert "str:" in row["type_mix"]


def test_strict_mode_correlation_is_not_always_zero():
    """
    Regression: score_correlation used to return 0.0 for any object-dtype column
    in strict mode. Two correlated mostly-numeric columns should produce a
    non-zero correlation score for both.
    """
    rng = np.random.default_rng(0)
    base = rng.normal(50, 10, 100)
    records = []
    for i, v in enumerate(base):
        # revenue is pure-float (pandas will infer float64); revenue_mixed has
        # one stray string to force object dtype.
        mixed = "N/A" if i == 0 else float(v + rng.normal(0, 1))
        records.append([float(v), mixed])
    df = _strict_frame_from_records(records, ["revenue", "revenue_mixed"])

    _, profiles, _, corr_df = analyze(df, strict_types=True)

    rev = profiles[profiles["field"] == "revenue"].iloc[0]
    mix = profiles[profiles["field"] == "revenue_mixed"].iloc[0]
    assert rev["correlation"] > 0.5, "clean numeric column should correlate with its mixed twin"
    assert mix["correlation"] > 0.5, "mixed-type column should correlate with its clean twin"
    # Correlation matrix should be a real matrix, not the "no numeric columns" placeholder.
    assert "note" not in corr_df.columns
    assert "revenue" in corr_df.columns
    assert "revenue_mixed" in corr_df.columns


def test_standard_mode_unchanged():
    """
    Standard mode reads via pandas, which coerces 'N/A' to NaN. revenue_mixed
    looks like a clean numeric column — same as before the fix.
    """
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "revenue": rng.lognormal(5, 1.5, 100).round(2),
        "category": (["a", "b", "c"] * 34)[:100],
    })

    rankings, profiles, _, _ = analyze(df, strict_types=False)

    rev = rankings[rankings["field"] == "revenue"].iloc[0]
    assert rev["field_type"] == "numeric_continuous"
    # In standard mode the rankings table doesn't include type_mix at all —
    # that column only appears in strict-mode output.
    assert "type_mix" not in rankings.columns


def test_strict_mode_boolean_column_detected_via_cell_types():
    """
    A column of Python bools should be classified as 'boolean' in strict mode,
    not coerced to numeric_discrete by pd.to_numeric.
    """
    records = [[True if i % 2 == 0 else False] for i in range(50)]
    df = pd.DataFrame(records, columns=["flag"])
    # In strict mode the loader leaves bool columns dtype=object; simulate that.
    df["flag"] = df["flag"].astype(object)

    rankings, _, _, _ = analyze(df, strict_types=True)
    row = rankings[rankings["field"] == "flag"].iloc[0]
    assert row["field_type"] == "boolean"


def test_correlation_matrix_present_when_multiple_numeric_columns():
    df = pd.DataFrame({
        "a": np.arange(50, dtype=float),
        "b": np.arange(50, dtype=float) * 2,
        "c": ["x"] * 50,
    })
    _, _, _, corr_df = analyze(df)
    assert "note" not in corr_df.columns
    assert set(corr_df.columns) == {"a", "b"}


def test_correlation_matrix_note_when_fewer_than_two_numeric():
    df = pd.DataFrame({
        "a": np.arange(10, dtype=float),
        "b": ["x"] * 10,
    })
    _, _, _, corr_df = analyze(df)
    assert "note" in corr_df.columns
