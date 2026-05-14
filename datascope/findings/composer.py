"""Template engine that populates the narrative text fields on a Finding.

Chooses the correct template function for each finding's sub-type (using
evidence keys to disambiguate within shared FindingType values) and writes
the five text fields onto the Finding in place.
"""

from __future__ import annotations

from datascope.models import Finding, FindingType
from datascope.findings import templates


# ---------------------------------------------------------------------------
# Sub-type dispatch
# ---------------------------------------------------------------------------

def _select_template(finding: Finding):
    """Return the template function for *finding*'s sub-type."""
    ft = finding.finding_type
    ev = finding.evidence

    if ft is FindingType.TYPE_INCONSISTENCY:
        return templates.type_inconsistency

    if ft is FindingType.SENTINEL_VALUE:
        return templates.sentinel_value

    if ft is FindingType.FORMAT_INCONSISTENCY:
        if "leading_zero_count" in ev:
            return templates.leading_zeros
        if "formats_found" in ev:
            return templates.mixed_dates
        # Fallback for unrecognised format sub-variant.
        return templates.leading_zeros

    if ft is FindingType.CARDINALITY_ANOMALY:
        if "top_values" in ev:
            return templates.near_constant
        if "duplicate_values" in ev:
            return templates.suspected_duplicate_ids
        # Fallback for unrecognised cardinality sub-variant.
        return templates.near_constant

    # Unknown finding type -- use type_inconsistency as a safe fallback
    # so that every finding always gets text populated.
    return templates.type_inconsistency


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_finding(finding: Finding) -> Finding:
    """Populate the narrative text fields on *finding* and return it.

    Selects the appropriate template based on the finding's type and
    evidence, then writes the five text fields (``assumption``,
    ``reality``, ``impact``, ``fix_recommendation``,
    ``prevention_rule``) onto the finding.

    Parameters
    ----------
    finding:
        A :class:`~datascope.models.Finding` with ``field_name``,
        ``finding_type``, and ``evidence`` populated.

    Returns
    -------
    Finding
        The same finding instance, now with all five text fields set.
    """
    template_fn = _select_template(finding)
    texts = template_fn(finding.field_name, finding.evidence)

    finding.assumption = texts["assumption"]
    finding.reality = texts["reality"]
    finding.impact = texts["impact"]
    finding.fix_recommendation = texts["fix_recommendation"]
    finding.prevention_rule = texts["prevention_rule"]

    return finding
