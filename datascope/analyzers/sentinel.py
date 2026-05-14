"""Sentinel-value detector.

Scans each column for hidden sentinel strings -- values like "N/A", "TBD",
or "pending" that lurk inside otherwise-typed columns.  Tools silently drop
or coerce these, so surfacing them early prevents data loss.

Produces a :class:`~datascope.models.Finding` for every non-string column
that contains sentinel values after frequency disambiguation.

Severity is *not* assigned here -- that is the severity classifier's job (U7).
"""

from __future__ import annotations

from collections import Counter

from datascope.models import Finding, FindingType, LoaderResult
from datascope.analyzers.type_consistency import normalize_type


# ---------------------------------------------------------------------------
# Default sentinel list
# ---------------------------------------------------------------------------

DEFAULT_SENTINELS: frozenset[str] = frozenset({
    "n/a",
    "na",
    "n.a.",
    "null",
    "none",
    "nil",
    "tbd",
    "pending",
    "unknown",
    "missing",
    "—",       # em-dash
    "-",
    ".",
    "..",
    "...",
    "#n/a",
    "#ref!",
    "#value!",
    "#div/0!",
    "#name?",
})


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

def analyze_sentinels(
    result: LoaderResult,
    sentinel_list: frozenset[str] | None = None,
) -> list[Finding]:
    """Detect hidden sentinel values in non-string columns.

    Parameters
    ----------
    result:
        A :class:`~datascope.models.LoaderResult` whose ``cell_types``
        dict maps column names to lists of Python ``type`` objects (one
        per row).
    sentinel_list:
        Optional custom set of lowercase sentinel strings to match
        against.  Defaults to :data:`DEFAULT_SENTINELS`.

    Returns
    -------
    list[Finding]
        One finding per non-string column that contains sentinel values
        (after frequency disambiguation).  String/categorical columns
        are skipped because sentinels there are not "hidden".
    """
    sentinels = sentinel_list if sentinel_list is not None else DEFAULT_SENTINELS
    findings: list[Finding] = []

    for col_name, types_list in result.cell_types.items():
        # 1. Determine majority type (ignoring NoneType)
        non_null_types = [t for t in types_list if t is not type(None)]
        if not non_null_types:
            continue

        normalized = [normalize_type(t) for t in non_null_types]
        type_counts = Counter(normalized)
        majority_type = type_counts.most_common(1)[0][0]

        # 2. Skip string/categorical columns -- sentinels are not hidden there
        if majority_type == "str":
            continue

        # 3. Scan cell values for sentinel matches
        col_values = list(result.dataframe[col_name])
        total_non_null = sum(
            1 for v in col_values if v is not None and str(v).strip() != ""
        )

        if total_non_null == 0:
            continue

        # Collect sentinel hits: track original-case value and count
        sentinel_hits: Counter[str] = Counter()  # lowercase -> count
        sentinel_originals: dict[str, str] = {}  # lowercase -> first original-case
        for val in col_values:
            if val is None:
                continue
            val_str = str(val)
            if not val_str.strip():
                continue
            val_lower = val_str.lower()
            if val_lower in sentinels:
                sentinel_hits[val_lower] += 1
                if val_lower not in sentinel_originals:
                    sentinel_originals[val_lower] = val_str

        if not sentinel_hits:
            continue

        # 4. Frequency disambiguation: if a specific sentinel is >50%
        #    of non-null values, treat it as a legitimate category
        surviving: dict[str, int] = {}
        for val_lower, count in sentinel_hits.items():
            if count / total_non_null <= 0.50:
                surviving[val_lower] = count
        sentinel_hits = Counter(surviving)

        if not sentinel_hits:
            continue

        # 5. Build evidence and produce Finding
        total_sentinel_count = sum(sentinel_hits.values())
        sentinel_pct = round(total_sentinel_count / total_non_null * 100, 2) if total_non_null else 0.0

        sentinels_found = [
            {
                "value": sentinel_originals[val_lower],
                "count": count,
                "normalized": val_lower,
            }
            for val_lower, count in sentinel_hits.most_common()
        ]

        evidence = {
            "sentinels_found": sentinels_found,
            "column_majority_type": majority_type,
            "total_non_null": total_non_null,
            "sentinel_pct": sentinel_pct,
        }

        findings.append(Finding(
            field_name=col_name,
            finding_type=FindingType.SENTINEL_VALUE,
            evidence=evidence,
        ))

    return findings
