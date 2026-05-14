"""Cardinality-anomaly detector.

Flags columns that are near-constant (very low uniqueness) or that look
like ID columns with unexpected duplicates (very high but not 100%
uniqueness).

Produces :class:`~datascope.models.Finding` instances with
:attr:`~datascope.models.FindingType.CARDINALITY_ANOMALY`.

Severity is *not* assigned here -- that is the severity classifier's job (U7).
"""

from __future__ import annotations

from collections import Counter

from datascope.models import Finding, FindingType, LoaderResult


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

_MIN_ROWS = 10             # Skip columns with fewer non-null rows
_NEAR_CONSTANT_MAX = 0.01  # uniqueness_ratio < this => near-constant
_SUSPECTED_ID_MIN = 0.95   # uniqueness_ratio > this AND < 1.0 => suspected-ID dups


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def analyze_cardinality(result: LoaderResult) -> list[Finding]:
    """Detect cardinality anomalies in each column.

    Two patterns are flagged:

    * **Near-constant**: fewer than 1% of values are unique.
    * **Suspected duplicate IDs**: more than 95% unique but less than
      100%, suggesting an ID column with unexpected duplicates.

    Columns with fewer than 10 non-null rows are skipped because
    cardinality ratios are unreliable for tiny samples.

    Parameters
    ----------
    result:
        A :class:`~datascope.models.LoaderResult`.

    Returns
    -------
    list[Finding]
        One finding per column that exhibits a cardinality anomaly.
    """
    findings: list[Finding] = []

    for col_name in result.dataframe.columns:
        series = result.dataframe[col_name]
        filled = series.dropna()
        total_count = len(filled)

        if total_count < _MIN_ROWS:
            continue

        unique_count = filled.nunique()
        uniqueness_ratio = round(unique_count / total_count, 4)

        if uniqueness_ratio < _NEAR_CONSTANT_MAX:
            # Near-constant column
            value_counts = Counter(filled)
            top_values = [
                {"value": str(val), "count": cnt}
                for val, cnt in value_counts.most_common(5)
            ]

            evidence = {
                "unique_count": unique_count,
                "total_count": total_count,
                "uniqueness_ratio": uniqueness_ratio,
                "top_values": top_values,
            }

            findings.append(Finding(
                field_name=col_name,
                finding_type=FindingType.CARDINALITY_ANOMALY,
                evidence=evidence,
            ))

        elif _SUSPECTED_ID_MIN < uniqueness_ratio < 1.0:
            # Suspected duplicate IDs
            value_counts = Counter(filled)
            duplicate_values = [
                str(val)
                for val, cnt in value_counts.most_common()
                if cnt > 1
            ][:10]

            evidence = {
                "unique_count": unique_count,
                "total_count": total_count,
                "uniqueness_ratio": uniqueness_ratio,
                "duplicate_values": duplicate_values,
            }

            findings.append(Finding(
                field_name=col_name,
                finding_type=FindingType.CARDINALITY_ANOMALY,
                evidence=evidence,
            ))

    return findings
