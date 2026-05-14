"""Severity classifier for datascope findings.

Maps each finding to a :class:`~datascope.models.Severity` level based on
the finding type and its evidence.  The rules are impact-based:

* **CRITICAL** -- silent data loss or incorrect calculations downstream.
* **WARNING** -- key mismatches or misinterpretation likely.
* **INFO** -- data quality concern without direct downstream breakage.

Severity is *not* assigned by detectors; this module is the single source
of truth for severity classification (U7).
"""

from __future__ import annotations

from datascope.models import Finding, FindingType, Severity

# Numeric types that can cause silent calculation errors when mixed.
_NUMERIC_TYPES: frozenset[str] = frozenset({"numeric", "int", "float"})


def _is_leading_zeros(evidence: dict) -> bool:
    """Return True if evidence belongs to a leading-zero finding."""
    return "leading_zero_count" in evidence


def _is_mixed_dates(evidence: dict) -> bool:
    """Return True if evidence belongs to a mixed-date finding."""
    return "formats_found" in evidence


def _is_near_constant(evidence: dict) -> bool:
    """Return True if evidence belongs to a near-constant cardinality finding."""
    return "top_values" in evidence


def _is_suspected_duplicates(evidence: dict) -> bool:
    """Return True if evidence belongs to a suspected-duplicate-ID finding."""
    return "duplicate_values" in evidence


def classify_severity(finding: Finding) -> Severity:
    """Determine the severity of *finding* based on its type and evidence.

    Parameters
    ----------
    finding:
        A :class:`~datascope.models.Finding` with ``finding_type`` and
        ``evidence`` populated.

    Returns
    -------
    Severity
        The computed severity level.
    """
    ft = finding.finding_type
    ev = finding.evidence

    if ft is FindingType.TYPE_INCONSISTENCY:
        majority = ev.get("majority_type", "")
        if majority.lower() in _NUMERIC_TYPES:
            return Severity.CRITICAL
        return Severity.WARNING

    if ft is FindingType.SENTINEL_VALUE:
        return Severity.CRITICAL

    if ft is FindingType.FORMAT_INCONSISTENCY:
        # Both sub-variants are WARNING.
        return Severity.WARNING

    if ft is FindingType.CARDINALITY_ANOMALY:
        if _is_near_constant(ev):
            return Severity.INFO
        if _is_suspected_duplicates(ev):
            return Severity.WARNING
        # Fallback for unrecognised cardinality evidence shape.
        return Severity.INFO

    # Unknown finding type -- default conservatively.
    return Severity.INFO
