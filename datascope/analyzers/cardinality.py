"""Cardinality-anomaly detector.

Flags columns that are near-constant (very low uniqueness) or that look
like ID columns with unexpected duplicates (very high but not 100%
uniqueness).

Produces :class:`~datascope.models.Finding` instances with
:attr:`~datascope.models.FindingType.NEAR_CONSTANT` or
:attr:`~datascope.models.FindingType.DUPLICATE_IDS`.

Severity is *not* assigned here -- that is the severity classifier's job (U7).
"""

from __future__ import annotations

import re
from collections import Counter

from datascope.models import Finding, FindingType, LoaderResult

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

_MIN_ROWS = 10             # Skip columns with fewer non-null rows
_DOMINANCE_MIN = 0.95      # one value covers >= this share of rows => near-constant
_SUSPECTED_ID_MIN = 0.95   # uniqueness_ratio > this AND < 1.0 => suspected-ID dups

# Name tokens that mark a column as an identifier.
_ID_WORDS = frozenset({
    "id", "ids", "uuid", "guid", "key", "pk", "fk", "code", "codes",
    "sku", "isbn", "upc", "ean", "ref", "acct", "account",
    "number", "no", "num",
})


def _tokenize(name: str) -> set[str]:
    """Split a column name into lowercase word tokens.

    Splits on non-alphanumeric boundaries *and* camelCase boundaries so
    that ``customerId``, ``record_id`` and ``ORDER-NO`` all yield an ID
    token.
    """
    tokens: list[str] = []
    for part in re.split(r"[^0-9A-Za-z]+", name):
        if not part:
            continue
        # Split camelCase / runs of caps / digit groups into sub-tokens.
        tokens.extend(
            re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+", part)
        )
    return {t.lower() for t in tokens}


def _is_integer_like(series) -> bool:
    """Return True if every non-null value looks like an integer.

    Ints and floats with no fractional part (e.g. ``3.0``) count.
    Booleans, strings and decimal-floats (e.g. ``3.14`` or
    :class:`decimal.Decimal`) do *not* — those are continuous measures or
    free text, not identifiers.
    """
    saw_value = False
    for val in series:
        saw_value = True
        if isinstance(val, bool):
            return False
        if isinstance(val, int):
            continue
        if isinstance(val, float):
            if not val.is_integer():
                return False
            continue
        return False
    return saw_value


def _looks_like_identifier(col_name: str, filled) -> bool:
    """A column is identifier-like if its name tokenizes to an ID word or
    its values are all integer-like."""
    if _tokenize(str(col_name)) & _ID_WORDS:
        return True
    return _is_integer_like(filled)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def analyze_cardinality(result: LoaderResult) -> list[Finding]:
    """Detect cardinality anomalies in each column.

    Two patterns are flagged:

    * **Near-constant**: one value dominates, covering >= 95% of the
      non-null rows (mode dominance).
    * **Suspected duplicate IDs**: more than 95% unique but less than
      100% *and* the column looks like an identifier (by name or by
      integer-like values), suggesting an ID column with unexpected
      duplicates. Continuous measures (e.g. revenue) are not flagged.

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

        value_counts = Counter(filled)
        top_count = value_counts.most_common(1)[0][1]
        dominance = top_count / total_count

        if dominance >= _DOMINANCE_MIN:
            # Near-constant column: one value dominates.
            top_values = [
                {"value": str(val), "count": cnt}
                for val, cnt in value_counts.most_common(5)
            ]

            evidence = {
                "unique_count": unique_count,
                "total_count": total_count,
                "uniqueness_ratio": uniqueness_ratio,
                "dominant_pct": round(dominance * 100, 2),
                "top_values": top_values,
            }

            findings.append(Finding(
                field_name=col_name,
                finding_type=FindingType.NEAR_CONSTANT,
                evidence=evidence,
            ))

        elif (
            _SUSPECTED_ID_MIN < uniqueness_ratio < 1.0
            and _looks_like_identifier(col_name, filled)
        ):
            # Suspected duplicate IDs (only for identifier-like columns).
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
                finding_type=FindingType.DUPLICATE_IDS,
                evidence=evidence,
            ))

    return findings
