"""Type-inconsistency detector.

Scans each column's ``cell_types`` for mixed Python types that pandas would
silently coerce.  Produces a :class:`~datascope.models.Finding` for every
column where more than one non-null type is present after normalization.

Severity is *not* assigned here -- that is the severity classifier's job.
The ``evidence`` dict carries all the raw counts and examples that
downstream stages (severity classifier, NL composer) need.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from datascope.models import Finding, FindingType, LoaderResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_type(t: type) -> str:
    """Map a Python type to a canonical bucket for type-consistency analysis.

    ``int`` and ``float`` are both mapped to ``"numeric"`` so that the
    openpyxl int-vs-float distinction (which is an artefact of the Excel
    number format, not a real type difference) does not create false
    positives.

    ``NoneType`` passes through unchanged -- callers filter it out before
    counting.
    """
    if t in (int, float):
        return "numeric"
    return t.__name__


def _examples_for_type(
    values: list[Any],
    cell_types: list[type],
    target_type: str,
    limit: int = 5,
) -> list[Any]:
    """Return up to *limit* example values whose normalized type matches *target_type*."""
    examples: list[Any] = []
    for val, ct in zip(values, cell_types):
        if normalize_type(ct) == target_type:
            examples.append(val)
            if len(examples) >= limit:
                break
    return examples


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def analyze_type_consistency(result: LoaderResult) -> list[Finding]:
    """Detect columns with mixed non-null types.

    Parameters
    ----------
    result:
        A :class:`~datascope.models.LoaderResult` whose ``cell_types``
        dict maps column names to lists of Python ``type`` objects (one
        per row).

    Returns
    -------
    list[Finding]
        One finding per column that has more than one distinct non-null
        type after normalization.  Columns that are homogeneous (or
        entirely null) produce no finding.
    """
    findings: list[Finding] = []

    for col_name, types_list in result.cell_types.items():
        # 1. Filter out NoneType (null cells don't count as a "type")
        non_null_types = [t for t in types_list if t is not type(None)]

        if not non_null_types:
            # All null -- nothing to report
            continue

        # 2. Normalize (collapse int/float -> "numeric")
        normalized = [normalize_type(t) for t in non_null_types]

        # 3. Count types after normalization
        counts = Counter(normalized)

        if len(counts) <= 1:
            # Homogeneous column -- no finding
            continue

        # 4. Multiple types detected -- build evidence
        total_non_null = len(non_null_types)
        majority_type = counts.most_common(1)[0][0]
        majority_count = counts[majority_type]
        majority_pct = round(majority_count / total_non_null * 100, 2)

        # Column values for gathering examples
        col_values = list(result.dataframe[col_name])

        # Build minority_types list (everything except majority)
        minority_types = []
        for type_name, count in counts.most_common():
            if type_name == majority_type:
                continue
            examples = _examples_for_type(
                col_values, types_list, type_name, limit=5,
            )
            minority_types.append({
                "type_name": type_name,
                "count": count,
                "examples": examples,
            })

        evidence = {
            "majority_type": majority_type,
            "majority_count": majority_count,
            "minority_types": minority_types,
            "total_non_null": total_non_null,
            "majority_pct": majority_pct,
        }

        findings.append(Finding(
            field_name=col_name,
            finding_type=FindingType.TYPE_INCONSISTENCY,
            evidence=evidence,
        ))

    return findings
