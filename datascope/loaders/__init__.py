"""datascope.loaders -- unified file loading with cell-level type tracking."""

from __future__ import annotations

from datascope.loaders.base import load
from datascope.loaders.csv_loader import load_csv
from datascope.loaders.excel import load_excel

__all__ = ["load", "load_csv", "load_excel"]
