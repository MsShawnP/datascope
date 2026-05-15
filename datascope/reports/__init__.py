"""datascope.reports -- render findings into deliverable report formats."""

from __future__ import annotations

from datascope.reports.annotated_excel import write_annotated_excel
from datascope.reports.html import write_html
from datascope.reports.pdf import write_pdf

__all__ = [
    "write_annotated_excel",
    "write_html",
    "write_pdf",
]
