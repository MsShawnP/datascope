"""Tests for datascope.analyzers.type_consistency -- the mixed-type detector."""

from __future__ import annotations

import pandas as pd
import pytest

from datascope.analyzers.type_consistency import (
    analyze_type_consistency,
    normalize_type,
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


# ---------------------------------------------------------------------------
# normalize_type
# ---------------------------------------------------------------------------

class TestNormalizeType:

    def test_int_maps_to_numeric(self):
        assert normalize_type(int) == "numeric"

    def test_float_maps_to_numeric(self):
        assert normalize_type(float) == "numeric"

    def test_str_maps_to_str(self):
        assert normalize_type(str) == "str"

    def test_bool_maps_to_bool(self):
        assert normalize_type(bool) == "bool"

    def test_nonetype_maps_to_nonetype(self):
        assert normalize_type(type(None)) == "NoneType"


# ---------------------------------------------------------------------------
# AE1 scenario: 485 numeric + 15 string
# ---------------------------------------------------------------------------

class TestAE1Scenario:
    """The core acceptance scenario -- a column that looks numeric but has
    a minority of string values hiding inside."""

    @pytest.fixture()
    def ae1_result(self) -> LoaderResult:
        values = [float(i) for i in range(485)] + [f"val_{i}" for i in range(15)]
        cell_types = [float] * 485 + [str] * 15
        return _make_loader_result("revenue", values, cell_types)

    def test_produces_one_finding(self, ae1_result):
        findings = analyze_type_consistency(ae1_result)
        assert len(findings) == 1

    def test_finding_field_name(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.field_name == "revenue"

    def test_finding_type(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.finding_type is FindingType.TYPE_INCONSISTENCY

    def test_severity_is_none(self, ae1_result):
        """Severity is assigned later by the classifier, not the detector."""
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.severity is None

    def test_evidence_majority_type(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.evidence["majority_type"] == "numeric"

    def test_evidence_majority_count(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.evidence["majority_count"] == 485

    def test_evidence_total_non_null(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.evidence["total_non_null"] == 500

    def test_evidence_majority_pct(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        assert finding.evidence["majority_pct"] == 97.0

    def test_evidence_minority_types(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        minority = finding.evidence["minority_types"]
        assert len(minority) == 1
        assert minority[0]["type_name"] == "str"
        assert minority[0]["count"] == 15

    def test_evidence_minority_examples(self, ae1_result):
        finding = analyze_type_consistency(ae1_result)[0]
        examples = finding.evidence["minority_types"][0]["examples"]
        assert len(examples) == 5
        assert all(isinstance(e, str) for e in examples)


# ---------------------------------------------------------------------------
# Happy paths (no finding expected)
# ---------------------------------------------------------------------------

class TestNoFinding:

    def test_all_numeric_column(self):
        """Column with all numeric values produces no finding."""
        values = [float(i) for i in range(100)]
        cell_types = [float] * 100
        result = _make_loader_result("price", values, cell_types)
        assert analyze_type_consistency(result) == []

    def test_all_string_column(self):
        """Column with all string values produces no finding."""
        values = [f"name_{i}" for i in range(50)]
        cell_types = [str] * 50
        result = _make_loader_result("name", values, cell_types)
        assert analyze_type_consistency(result) == []


# ---------------------------------------------------------------------------
# 50/50 split
# ---------------------------------------------------------------------------

class TestFiftySplit:

    def test_fifty_fifty_produces_finding(self):
        """50 numeric + 50 string still produces a finding."""
        values = [float(i) for i in range(50)] + [f"s_{i}" for i in range(50)]
        cell_types = [float] * 50 + [str] * 50
        result = _make_loader_result("mixed", values, cell_types)
        findings = analyze_type_consistency(result)
        assert len(findings) == 1

    def test_fifty_fifty_majority_pct(self):
        values = [float(i) for i in range(50)] + [f"s_{i}" for i in range(50)]
        cell_types = [float] * 50 + [str] * 50
        result = _make_loader_result("mixed", values, cell_types)
        finding = analyze_type_consistency(result)[0]
        assert finding.evidence["majority_pct"] == 50.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestIntFloatNormalization:
    """int and float should collapse to 'numeric' -- no false positive."""

    def test_mixed_int_float_no_finding(self):
        values = [1, 2.5, 3, 4.0, 5]
        cell_types = [int, float, int, float, int]
        result = _make_loader_result("amount", values, cell_types)
        assert analyze_type_consistency(result) == []


class TestBoolAndString:

    def test_bool_string_produces_finding(self):
        values = [True, False, "yes", True, "no"]
        cell_types = [bool, bool, str, bool, str]
        result = _make_loader_result("active", values, cell_types)
        findings = analyze_type_consistency(result)
        assert len(findings) == 1
        finding = findings[0]
        assert finding.evidence["majority_type"] == "bool"
        assert finding.evidence["majority_count"] == 3
        assert finding.evidence["minority_types"][0]["type_name"] == "str"
        assert finding.evidence["minority_types"][0]["count"] == 2


class TestAllNull:

    def test_all_none_no_finding(self):
        """Column with all None values produces no finding."""
        values = [None, None, None, None]
        cell_types = [type(None), type(None), type(None), type(None)]
        result = _make_loader_result("empty", values, cell_types)
        assert analyze_type_consistency(result) == []


class TestSingleRow:

    def test_single_row_no_finding(self):
        """A single non-null cell can't be inconsistent with itself."""
        values = [42]
        cell_types = [int]
        result = _make_loader_result("solo", values, cell_types)
        assert analyze_type_consistency(result) == []


class TestNullMinorityIgnored:

    def test_nulls_plus_one_type_no_finding(self):
        """If the only non-null type is one kind, nulls don't trigger a finding."""
        values = [1.0, None, 2.0, None, 3.0]
        cell_types = [float, type(None), float, type(None), float]
        result = _make_loader_result("sparse", values, cell_types)
        assert analyze_type_consistency(result) == []

    def test_nulls_with_mixed_non_null_produces_finding(self):
        """Nulls are filtered; the remaining types are still mixed."""
        values = [1.0, None, "oops", None, 3.0]
        cell_types = [float, type(None), str, type(None), float]
        result = _make_loader_result("sparse_mixed", values, cell_types)
        findings = analyze_type_consistency(result)
        assert len(findings) == 1
        assert findings[0].evidence["total_non_null"] == 3


# ---------------------------------------------------------------------------
# Multi-column: only mixed columns produce findings
# ---------------------------------------------------------------------------

class TestMultiColumn:

    def test_mixed_and_clean_columns(self):
        """Two columns: one mixed, one clean.  Only the mixed one gets a finding."""
        df = pd.DataFrame(
            {"clean": [1, 2, 3], "dirty": [1, "two", 3]},
            dtype=object,
        )
        result = LoaderResult(
            dataframe=df,
            cell_types={
                "clean": [int, int, int],
                "dirty": [int, str, int],
            },
        )
        findings = analyze_type_consistency(result)
        assert len(findings) == 1
        assert findings[0].field_name == "dirty"


# ---------------------------------------------------------------------------
# Empty cell_types (no columns at all)
# ---------------------------------------------------------------------------

class TestEmptyInput:

    def test_empty_cell_types(self):
        result = LoaderResult(dataframe=pd.DataFrame(), cell_types={})
        assert analyze_type_consistency(result) == []
