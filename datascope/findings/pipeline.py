"""Finding processing pipeline -- classify, compose, and sort.

Provides the main entry point :func:`process_findings` that takes raw
findings from the analyzers and returns them fully enriched and sorted
for report output.
"""

from __future__ import annotations

from datascope.models import Finding
from datascope.findings.severity import classify_severity
from datascope.findings.composer import compose_finding


def process_findings(findings: list[Finding]) -> list[Finding]:
    """Classify, compose, and sort a list of findings.

    1. Assigns a severity to each finding via :func:`classify_severity`.
    2. Populates narrative text fields via :func:`compose_finding`.
    3. Sorts by severity descending (CRITICAL first), then by
       ``field_name`` alphabetically within each severity tier (R12).

    Parameters
    ----------
    findings:
        Raw findings from the analyzers with ``finding_type`` and
        ``evidence`` populated but ``severity`` and text fields as None.

    Returns
    -------
    list[Finding]
        The same finding objects, now fully enriched, in sorted order.
    """
    for finding in findings:
        finding.severity = classify_severity(finding)
        compose_finding(finding)

    findings.sort(key=lambda f: (-f.severity.value, f.field_name))
    return findings
