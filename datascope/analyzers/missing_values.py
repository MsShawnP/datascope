"""Missing-value pattern detector.

Scans each column for significant null/blank concentrations and flags
columns where missingness exceeds a configurable threshold.  Also detects
rows that are entirely null (likely empty rows from a source extract).

Produces :class:`~datascope.models.Finding` instances with
:attr:`~datascope.models.FindingType.MISSING_VALUE_PATTERN`.
"""

from __future__ import annotations

import pandas as pd

from datascope.models import Finding, FindingType, LoaderResult

_DEFAULT_THRESHOLD_PCT = 10.0


def analyze_missing_values(
    result: LoaderResult,
    threshold_pct: float = _DEFAULT_THRESHOLD_PCT,
) -> list[Finding]:
    """Detect columns with significant missing-value patterns.

    Parameters
    ----------
    result:
        A :class:`~datascope.models.LoaderResult` with a populated DataFrame.
    threshold_pct:
        Minimum percentage of nulls in a column to produce a finding.
        Default: 10%.

    Returns
    -------
    list[Finding]
        One finding per column that exceeds the null threshold.
    """
    df = result.dataframe
    if df.empty:
        return []

    findings: list[Finding] = []
    total_rows = len(df)

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count == 0:
            continue

        null_pct = round(null_count / total_rows * 100, 2)
        if null_pct < threshold_pct:
            continue

        non_null_count = total_rows - null_count
        null_positions = _sample_null_positions(df[col])
        distribution = _null_distribution(df[col], total_rows)

        evidence = {
            "null_count": null_count,
            "total_rows": total_rows,
            "null_pct": null_pct,
            "non_null_count": non_null_count,
            "sample_null_positions": null_positions,
            "distribution": distribution,
        }

        findings.append(Finding(
            field_name=str(col),
            finding_type=FindingType.MISSING_VALUE_PATTERN,
            evidence=evidence,
        ))

    return findings


def _sample_null_positions(series: pd.Series, limit: int = 5) -> list[int]:
    """Return up to *limit* 0-based row indices where the series is null."""
    nulls = series[series.isna()]
    return list(nulls.index[:limit])


def _null_distribution(series: pd.Series, total_rows: int) -> str:
    """Characterize where nulls appear: beginning, end, scattered, or contiguous."""
    null_mask = series.isna()
    null_indices = null_mask[null_mask].index.tolist()
    if not null_indices:
        return "none"

    n = len(null_indices)
    midpoint = total_rows // 2

    early = sum(1 for i in null_indices if i < midpoint)
    late = n - early

    if early > n * 0.7:
        return "concentrated at start"
    if late > n * 0.7:
        return "concentrated at end"

    if n > 1:
        diffs = [null_indices[i + 1] - null_indices[i] for i in range(n - 1)]
        if all(d == 1 for d in diffs):
            return "contiguous block"

    return "scattered"
