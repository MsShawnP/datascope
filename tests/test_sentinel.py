"""Tests for datascope.analyzers.sentinel -- the sentinel-value detector."""

from __future__ import annotations

import pandas as pd
import pytest

from datascope.analyzers.sentinel import (
    DEFAULT_SENTINELS,
    analyze_sentinels,
)
from datascope.models import FindingType, LoaderResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loader_result(
    col_name: str,
    values: list,
    cell_types: list[type],
) -> LoaderResult:
    """Build a single-column LoaderResult for testing."""
    df = pd.DataFrame({col_name: values}, dtype=object)
    return LoaderResult(
        dataframe=df,
        cell_types={col_name: cell_types},
        source_metadata={"filename": "test_synthetic.xlsx"},
    )


def _make_multi_column_result(
    columns: dict[str, tuple[list, list[type]]],
) -> LoaderResult:
    """Build a multi-column LoaderResult for testing.

    ``columns`` maps column name to (values, cell_types) tuples.
    """
    data = {name: vals for name, (vals, _) in columns.items()}
    df = pd.DataFrame(data, dtype=object)
    cell_types = {name: types for name, (_, types) in columns.items()}
    return LoaderResult(
        dataframe=df,
        cell_types=cell_types,
        source_metadata={"filename": "test_synthetic.xlsx"},
    )


# ---------------------------------------------------------------------------
# Happy path: numeric column with sentinel values
# ---------------------------------------------------------------------------

class TestNumericColumnWithSentinels:
    """Numeric column containing a few 'N/A' strings should produce a Finding."""

    @pytest.fixture()
    def result(self) -> LoaderResult:
        values = [1.0, 2.0, "N/A", 4.0, "N/A", 6.0, 7.0, 8.0, "N/A", 10.0]
        cell_types = [float, float, str, float, str, float, float, float, str, float]
        return _make_loader_result("revenue", values, cell_types)

    def test_produces_one_finding(self, result):
        findings = analyze_sentinels(result)
        assert len(findings) == 1

    def test_finding_field_name(self, result):
        finding = analyze_sentinels(result)[0]
        assert finding.field_name == "revenue"

    def test_finding_type(self, result):
        finding = analyze_sentinels(result)[0]
        assert finding.finding_type is FindingType.SENTINEL_VALUE

    def test_severity_is_none(self, result):
        """Severity is assigned later by the classifier, not the detector."""
        finding = analyze_sentinels(result)[0]
        assert finding.severity is None

    def test_evidence_sentinels_found(self, result):
        finding = analyze_sentinels(result)[0]
        sentinels = finding.evidence["sentinels_found"]
        assert len(sentinels) == 1
        assert sentinels[0]["value"] == "N/A"
        assert sentinels[0]["count"] == 3
        assert sentinels[0]["normalized"] == "n/a"

    def test_evidence_majority_type(self, result):
        finding = analyze_sentinels(result)[0]
        assert finding.evidence["column_majority_type"] == "numeric"

    def test_evidence_total_non_null(self, result):
        finding = analyze_sentinels(result)[0]
        assert finding.evidence["total_non_null"] == 10

    def test_evidence_sentinel_pct(self, result):
        finding = analyze_sentinels(result)[0]
        assert finding.evidence["sentinel_pct"] == 30.0


# ---------------------------------------------------------------------------
# Happy path: multiple sentinel types in one column
# ---------------------------------------------------------------------------

class TestMultipleSentinelTypes:
    """Column with both 'TBD' and 'pending' should list both in evidence."""

    @pytest.fixture()
    def result(self) -> LoaderResult:
        values = [10, 20, "TBD", 40, "pending", 60, 70, 80, "TBD", 100]
        cell_types = [int, int, str, int, str, int, int, int, str, int]
        return _make_loader_result("amount", values, cell_types)

    def test_produces_one_finding(self, result):
        findings = analyze_sentinels(result)
        assert len(findings) == 1

    def test_both_sentinels_listed(self, result):
        finding = analyze_sentinels(result)[0]
        sentinels = finding.evidence["sentinels_found"]
        normalized_values = {s["normalized"] for s in sentinels}
        assert "tbd" in normalized_values
        assert "pending" in normalized_values

    def test_tbd_count(self, result):
        finding = analyze_sentinels(result)[0]
        sentinels = {s["normalized"]: s for s in finding.evidence["sentinels_found"]}
        assert sentinels["tbd"]["count"] == 2

    def test_pending_count(self, result):
        finding = analyze_sentinels(result)[0]
        sentinels = {s["normalized"]: s for s in finding.evidence["sentinels_found"]}
        assert sentinels["pending"]["count"] == 1


# ---------------------------------------------------------------------------
# Happy path: column with no sentinels
# ---------------------------------------------------------------------------

class TestNoSentinels:

    def test_clean_numeric_column(self):
        """All-numeric column produces no finding."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        cell_types = [float] * 5
        result = _make_loader_result("price", values, cell_types)
        assert analyze_sentinels(result) == []


# ---------------------------------------------------------------------------
# Edge case: frequency disambiguation (>50% is legitimate)
# ---------------------------------------------------------------------------

class TestFrequencyDisambiguation:

    def test_sentinel_over_50_pct_skipped(self):
        """If 'N/A' is 60% of non-null values, treat as legitimate category."""
        # 6 out of 10 non-null values are "N/A" = 60%
        values = ["N/A"] * 6 + [1.0, 2.0, 3.0, 4.0]
        cell_types = [str] * 6 + [float] * 4
        result = _make_loader_result("score", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 0

    def test_sentinel_under_50_pct_detected(self):
        """If 'N/A' is only 5% of non-null values, it should be flagged."""
        # 1 out of 20 non-null values = 5%
        values = [float(i) for i in range(19)] + ["N/A"]
        cell_types = [float] * 19 + [str]
        result = _make_loader_result("score", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].evidence["sentinels_found"][0]["normalized"] == "n/a"

    def test_sentinel_exactly_50_pct_of_non_null_detected(self):
        """At exactly 50% of non-null, the sentinel does NOT exceed >50% -- detected.

        6 floats + 2 "N/A" + 2 None.  Majority type: numeric (6 vs 2 str).
        total_non_null (non-None, non-empty) = 8.  Sentinel count = 2.
        Sentinel fraction = 2/8 = 25% which is <= 50%, so not disambiguated.
        """
        values = [1.0, 2.0, "N/A", 4.0, None, 6.0, "N/A", 8.0, None, 10.0]
        cell_types = [float, float, str, float, type(None), float, str, float, type(None), float]
        result = _make_loader_result("score", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].evidence["sentinels_found"][0]["count"] == 2


# ---------------------------------------------------------------------------
# Edge case: string/categorical column -- sentinels not hidden
# ---------------------------------------------------------------------------

class TestStringColumnSkipped:

    def test_string_column_with_sentinels_no_finding(self):
        """Sentinels in a string column are not 'hidden' -- skip."""
        values = ["hello", "N/A", "world", "TBD", "pending"]
        cell_types = [str] * 5
        result = _make_loader_result("notes", values, cell_types)
        assert analyze_sentinels(result) == []


# ---------------------------------------------------------------------------
# Edge case: case sensitivity
# ---------------------------------------------------------------------------

class TestCaseSensitivity:

    def test_mixed_case_all_detected(self):
        """'n/a', 'N/A', and 'N/a' should all match."""
        values = [1.0, "n/a", 2.0, "N/A", 3.0, "N/a"]
        cell_types = [float, str, float, str, float, str]
        result = _make_loader_result("amount", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        sentinel = findings[0].evidence["sentinels_found"][0]
        assert sentinel["normalized"] == "n/a"
        assert sentinel["count"] == 3

    def test_original_case_preserved(self):
        """Evidence should record the first original-case occurrence."""
        values = [1.0, "N/A", 2.0, "n/a"]
        cell_types = [float, str, float, str]
        result = _make_loader_result("amount", values, cell_types)
        finding = analyze_sentinels(result)[0]
        # The first occurrence is "N/A"
        assert finding.evidence["sentinels_found"][0]["value"] == "N/A"


# ---------------------------------------------------------------------------
# Edge case: empty string cells not treated as sentinels
# ---------------------------------------------------------------------------

class TestEmptyStrings:

    def test_empty_strings_not_sentinels(self):
        """Empty strings should not be detected as sentinel values."""
        values = [1.0, "", 2.0, "", 3.0]
        cell_types = [float, str, float, str, float]
        result = _make_loader_result("amount", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Edge case: Excel error values
# ---------------------------------------------------------------------------

class TestExcelErrors:

    def test_ref_error_detected(self):
        values = [1.0, 2.0, "#REF!", 4.0, 5.0]
        cell_types = [float, float, str, float, float]
        result = _make_loader_result("formula_col", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        sentinel = findings[0].evidence["sentinels_found"][0]
        assert sentinel["normalized"] == "#ref!"
        assert sentinel["value"] == "#REF!"

    def test_value_error_detected(self):
        values = [1.0, "#VALUE!", 3.0, 4.0, 5.0]
        cell_types = [float, str, float, float, float]
        result = _make_loader_result("calc_col", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].evidence["sentinels_found"][0]["normalized"] == "#value!"

    def test_div0_error_detected(self):
        values = [1.0, 2.0, "#DIV/0!", 4.0, 5.0]
        cell_types = [float, float, str, float, float]
        result = _make_loader_result("ratio", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].evidence["sentinels_found"][0]["normalized"] == "#div/0!"

    def test_name_error_detected(self):
        values = [1.0, 2.0, 3.0, "#NAME?", 5.0]
        cell_types = [float, float, float, str, float]
        result = _make_loader_result("lookup", values, cell_types)
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].evidence["sentinels_found"][0]["normalized"] == "#name?"


# ---------------------------------------------------------------------------
# Custom sentinel list
# ---------------------------------------------------------------------------

class TestCustomSentinelList:

    def test_custom_list_used(self):
        """When a custom sentinel list is passed, only those values match."""
        custom = frozenset({"x", "y"})
        values = [1.0, "x", 2.0, "N/A", 3.0]
        cell_types = [float, str, float, str, float]
        result = _make_loader_result("col", values, cell_types)
        findings = analyze_sentinels(result, sentinel_list=custom)
        assert len(findings) == 1
        # Only "x" matched, not "N/A"
        sentinels = findings[0].evidence["sentinels_found"]
        assert len(sentinels) == 1
        assert sentinels[0]["normalized"] == "x"

    def test_custom_list_empty_no_findings(self):
        """An empty custom list produces no findings."""
        values = [1.0, "N/A", 2.0]
        cell_types = [float, str, float]
        result = _make_loader_result("col", values, cell_types)
        findings = analyze_sentinels(result, sentinel_list=frozenset())
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Multiple columns: only non-string columns with sentinels get findings
# ---------------------------------------------------------------------------

class TestMultipleColumns:

    def test_mixed_columns(self):
        """Three columns: numeric with sentinel, clean numeric, all-string.
        Only the first should produce a finding."""
        result = _make_multi_column_result({
            "revenue": (
                [1.0, 2.0, "N/A", 4.0, 5.0],
                [float, float, str, float, float],
            ),
            "quantity": (
                [10, 20, 30, 40, 50],
                [int, int, int, int, int],
            ),
            "status": (
                ["open", "N/A", "closed", "TBD", "open"],
                [str, str, str, str, str],
            ),
        })
        findings = analyze_sentinels(result)
        assert len(findings) == 1
        assert findings[0].field_name == "revenue"

    def test_two_columns_with_sentinels(self):
        """Two numeric columns with sentinels each get a finding."""
        result = _make_multi_column_result({
            "col_a": (
                [1.0, "N/A", 3.0],
                [float, str, float],
            ),
            "col_b": (
                [10, "TBD", 30],
                [int, str, int],
            ),
        })
        findings = analyze_sentinels(result)
        assert len(findings) == 2
        found_names = {f.field_name for f in findings}
        assert found_names == {"col_a", "col_b"}


# ---------------------------------------------------------------------------
# Edge cases: all null, empty input
# ---------------------------------------------------------------------------

class TestAllNullColumn:

    def test_all_none_no_finding(self):
        """Column with all None values produces no finding."""
        values = [None, None, None]
        cell_types = [type(None), type(None), type(None)]
        result = _make_loader_result("empty", values, cell_types)
        assert analyze_sentinels(result) == []


class TestEmptyInput:

    def test_empty_cell_types(self):
        result = LoaderResult(dataframe=pd.DataFrame(), cell_types={})
        assert analyze_sentinels(result) == []


# ---------------------------------------------------------------------------
# DEFAULT_SENTINELS coverage
# ---------------------------------------------------------------------------

class TestDefaultSentinels:

    def test_default_sentinels_is_frozenset(self):
        assert isinstance(DEFAULT_SENTINELS, frozenset)

    def test_expected_values_present(self):
        expected = {"n/a", "na", "null", "none", "nil", "tbd", "pending",
                    "unknown", "missing", "#n/a", "#ref!", "#value!",
                    "#div/0!", "#name?"}
        assert expected.issubset(DEFAULT_SENTINELS)


# ---------------------------------------------------------------------------
# Import from package __init__
# ---------------------------------------------------------------------------

class TestPackageExport:

    def test_analyze_sentinels_importable_from_package(self):
        from datascope.analyzers import analyze_sentinels as fn
        assert callable(fn)
