"""datascope.findings -- severity classification and narrative composition.

This package enriches raw :class:`~datascope.models.Finding` objects
produced by the analyzers with:

* **severity** -- an impact-based classification (CRITICAL / WARNING / INFO)
* **narrative text** -- five plain-English fields that explain the finding
  in an assumption-vs-reality framing.
"""

from __future__ import annotations

from datascope.findings.composer import compose_finding
from datascope.findings.pipeline import process_findings
from datascope.findings.severity import classify_severity

__all__ = [
    "classify_severity",
    "compose_finding",
    "process_findings",
]
