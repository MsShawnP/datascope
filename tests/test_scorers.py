"""Unit tests for the per-dimension scoring functions in scorer.py."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from scorer import (
    WEIGHTS,
    composite_score,
    infer_field_type,
    recommend_chart,
    score_cardinality,
    score_completeness,
    score_correlation,
    score_distribution,
    score_type_consistency,
)


# ---------------------------------------------------------------------------
# score_completeness
# ---------------------------------------------------------------------------

def test_completeness_full():
    assert score_completeness(pd.Series([1, 2, 3, 4])) == 1.0


def test_completeness_half():
    assert score_completeness(pd.Series([1, None, 2, None])) == 0.5


def test_completeness_all_null():
    assert score_completeness(pd.Series([None, None, None])) == 0.0


def test_completeness_empty():
    assert score_completeness(pd.Series([], dtype=object)) == 0.0


# ---------------------------------------------------------------------------
# score_cardinality
# ---------------------------------------------------------------------------

def test_cardinality_constant():
    assert score_cardinality(pd.Series(["x"] * 10)) == pytest.approx(0.1)


def test_cardinality_all_unique():
    assert score_cardinality(pd.Series(list(range(10)))) == 1.0


def test_cardinality_ignores_nulls():
    # 3 distinct values among 4 non-null cells; the None is dropped.
    assert score_cardinality(pd.Series([1, 2, 3, 3, None])) == pytest.approx(0.75)


def test_cardinality_all_null():
    assert score_cardinality(pd.Series([None, None])) == 0.0


# ---------------------------------------------------------------------------
# score_type_consistency
# ---------------------------------------------------------------------------

def test_type_consistency_numeric_dtype_trusts_pandas():
    # Numeric dtype short-circuits to 1.0 (pandas has already enforced the type).
    assert score_type_consistency(pd.Series([1.0, 2.0, 3.0])) == 1.0


def test_type_consistency_object_homogeneous():
    assert score_type_consistency(pd.Series(["a", "b", "c"], dtype=object)) == 1.0


def test_type_consistency_object_majority_numeric():
    # 9 numeric values, 1 string → 0.9 (int and float collapse into one bucket).
    s = pd.Series([1, 2, 3.0, 4, 5, 6, 7, 8, 9, "N/A"], dtype=object)
    assert score_type_consistency(s) == pytest.approx(0.9, abs=1e-4)


def test_type_consistency_empty():
    assert score_type_consistency(pd.Series([], dtype=object)) == 1.0


# ---------------------------------------------------------------------------
# score_distribution
# ---------------------------------------------------------------------------

def test_distribution_numeric_constant_is_zero():
    assert score_distribution(pd.Series([5.0] * 20)) == 0.0


def test_distribution_numeric_varying_caps_at_one():
    # Lognormal with sigma=1.5 has CV >> 1, so the score should saturate at 1.0.
    rng = np.random.default_rng(0)
    s = pd.Series(rng.lognormal(mean=5, sigma=1.5, size=500))
    assert score_distribution(s) == 1.0


def test_distribution_categorical_uniform_is_one():
    s = pd.Series(["a", "b", "c", "d"] * 10, dtype=object)
    assert score_distribution(s) == pytest.approx(1.0, abs=1e-4)


def test_distribution_categorical_single_value_is_zero():
    s = pd.Series(["x"] * 10, dtype=object)
    assert score_distribution(s) == 0.0


def test_distribution_uses_numeric_view_when_provided():
    # The series is object-dtype with a sentinel string; the numeric_view
    # carries the coerced numeric values so CV can be computed.
    raw = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, "N/A"], dtype=object)
    numeric_view = pd.to_numeric(raw, errors="coerce")
    score = score_distribution(raw, numeric_view=numeric_view)
    # Without numeric_view this would compute entropy across mostly-unique values
    # and return ~1.0; with the view it should compute CV of the numeric subset.
    # CV of 1..9 (mean=5, std≈2.74) ≈ 0.548 — well under 1.
    assert 0.4 < score < 0.7


# ---------------------------------------------------------------------------
# score_correlation
# ---------------------------------------------------------------------------

def test_correlation_empty_matrix():
    assert score_correlation("foo", pd.DataFrame()) == 0.0


def test_correlation_missing_column():
    cm = pd.DataFrame({"a": [1.0, 0.5], "b": [0.5, 1.0]}, index=["a", "b"])
    assert score_correlation("c", cm) == 0.0


def test_correlation_perfect_pair():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [2.0, 4.0, 6.0, 8.0]})
    cm = df.corr()
    # a vs b is +1.0; mean abs corr (excluding self) is 1.0.
    assert score_correlation("a", cm) == 1.0


def test_correlation_independent_pair():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"a": rng.normal(size=500), "b": rng.normal(size=500)})
    cm = df.corr()
    assert score_correlation("a", cm) < 0.2


# ---------------------------------------------------------------------------
# infer_field_type
# ---------------------------------------------------------------------------

def test_infer_numeric_continuous():
    assert infer_field_type(pd.Series(np.arange(100))) == "numeric_continuous"


def test_infer_numeric_discrete():
    assert infer_field_type(pd.Series([1, 2, 3, 1, 2, 3])) == "numeric_discrete"


def test_infer_boolean():
    assert infer_field_type(pd.Series([True, False, True])) == "boolean"


def test_infer_datetime():
    s = pd.Series(pd.date_range("2024-01-01", periods=10))
    assert infer_field_type(s) == "datetime"


def test_infer_identifier_high_unique_ratio():
    s = pd.Series([f"id_{i}" for i in range(100)], dtype=object)
    assert infer_field_type(s) == "identifier"


def test_infer_categorical_low():
    s = pd.Series(["a", "b", "c"] * 50, dtype=object)
    assert infer_field_type(s) == "categorical_low"


def test_infer_unknown_all_null():
    assert infer_field_type(pd.Series([None] * 5, dtype=object)) == "unknown"


def test_infer_numeric_view_overrides_object_dtype():
    # The strict-mode regression — object dtype with a numeric_view should be
    # classified as numeric, not as identifier.
    raw = pd.Series([float(i) for i in range(100)] + ["N/A"], dtype=object)
    numeric_view = pd.to_numeric(raw, errors="coerce")
    assert infer_field_type(raw, numeric_view=numeric_view) == "numeric_continuous"


def test_infer_force_type_wins():
    # force_type short-circuits everything else (used for bool/datetime in strict mode).
    s = pd.Series([1, 2, 3])
    assert infer_field_type(s, force_type="boolean") == "boolean"


# ---------------------------------------------------------------------------
# recommend_chart
# ---------------------------------------------------------------------------

def test_recommend_chart_identifier_no_redundant_warning():
    # The "All unique" warning must not be appended when the field is already
    # classified as identifier — that text appears in the base recommendation.
    rec = recommend_chart("identifier", cardinality=1.0, distribution=0.5)
    assert "⚠ All unique" not in rec
    assert "not recommended for visualization" in rec


def test_recommend_chart_categorical_all_unique_gets_warning():
    rec = recommend_chart("categorical_high", cardinality=1.0, distribution=0.5)
    assert "⚠ All unique" in rec


def test_recommend_chart_near_constant_warning():
    rec = recommend_chart("categorical_low", cardinality=0.005, distribution=0.0)
    assert "Near-constant" in rec


# ---------------------------------------------------------------------------
# composite_score
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_composite_all_ones():
    perfect = {k: 1.0 for k in WEIGHTS}
    assert composite_score(perfect) == 1.0


def test_composite_all_zeros():
    zero = {k: 0.0 for k in WEIGHTS}
    assert composite_score(zero) == 0.0


def test_composite_weighted_sum():
    row = {
        "completeness": 1.0,
        "cardinality": 0.0,
        "type_consistency": 1.0,
        "distribution": 0.0,
        "correlation": 0.0,
    }
    # 0.30*1 + 0.15*0 + 0.25*1 + 0.15*0 + 0.15*0 = 0.55
    assert composite_score(row) == pytest.approx(0.55)
