"""CSV loader -- cell-level type inference from raw text.

CSV has no native type metadata, so each cell is parsed through an
inference pipeline that is *functionally equivalent* to what openpyxl
provides for Excel files.  The int-vs-float distinction may differ
because CSV cannot distinguish ``1`` from ``1.0`` at the format level.

Returns a :class:`~datascope.models.LoaderResult` identical in shape to
the Excel loader.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from datascope.models import LoaderResult

# Canonical boolean strings (case-insensitive).
_BOOL_TRUE = frozenset({"true", "yes"})
_BOOL_FALSE = frozenset({"false", "no"})

# Date/time formats tried in order (most specific first).
_DATETIME_FMTS = (
    "%Y-%m-%dT%H:%M:%S",      # ISO 8601
    "%Y-%m-%d %H:%M:%S",      # space-separated
    "%Y-%m-%d",                # date only
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
)

_DATE_LIKE_RE = re.compile(
    r"^\d{1,4}[\-/\.]\d{1,2}[\-/\.]\d{1,4}"
    r"(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?$"
    r"|^\w+ \d{1,2},? \d{2,4}$"
    r"|^\d{1,2} \w+ \d{2,4}$"
)


def _infer_cell(raw: str) -> object:
    """Infer a single cell's Python value from its raw CSV string.

    Inference order:
    1. Empty / whitespace -> ``None``
    2. Integer
    3. Float
    4. Boolean (true/false/yes/no, case-insensitive)
    5. Datetime (common formats)
    6. String fallback
    """
    stripped = raw.strip()
    if not stripped:
        return None

    # Preserve leading-zero digit strings (e.g. "00123") as strings
    # so the leading-zero analyzer can detect the inconsistency.
    if len(stripped) > 1 and stripped[0] == "0" and stripped.isdigit():
        return stripped

    # --- int ----------------------------------------------------------
    try:
        return int(stripped)
    except ValueError:
        pass

    # --- float --------------------------------------------------------
    try:
        return float(stripped)
    except ValueError:
        pass

    # --- bool ---------------------------------------------------------
    lower = stripped.lower()
    if lower in _BOOL_TRUE:
        return True
    if lower in _BOOL_FALSE:
        return False

    # --- datetime -----------------------------------------------------
    if _DATE_LIKE_RE.match(stripped):
        for fmt in _DATETIME_FMTS:
            try:
                return datetime.strptime(stripped, fmt)
            except ValueError:
                continue

    # --- string fallback ----------------------------------------------
    return stripped


def load_csv(path: Path) -> LoaderResult:
    """Read a CSV file with per-cell type inference.

    Parameters
    ----------
    path:
        Path to the ``.csv`` file.  UTF-8-BOM is handled transparently
        via ``encoding="utf-8-sig"``.

    Returns
    -------
    LoaderResult
        DataFrame with ``dtype=object`` (values are inferred Python types),
        per-column ``cell_types``, and source metadata.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file is empty (no header row) or malformed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            first_row = next(reader, None)

            if first_row is None:
                return LoaderResult(
                    dataframe=pd.DataFrame(),
                    cell_types={},
                    source_metadata={
                        "filename": path.name,
                        "row_count": 0,
                        "column_count": 0,
                    },
                )

            headers = [
                h.strip() if h.strip() else f"col_{i}"
                for i, h in enumerate(first_row)
            ]
            n_cols = len(headers)

            # Single-pass: infer types and build column-major type lists
            col_types: list[list[type]] = [[] for _ in range(n_cols)]
            inferred_rows: list[list[object]] = []

            for raw_row in reader:
                padded = raw_row + [""] * max(0, n_cols - len(raw_row))
                row = [_infer_cell(padded[i]) for i in range(n_cols)]
                inferred_rows.append(row)
                for i in range(n_cols):
                    col_types[i].append(type(row[i]))

    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc

    if not inferred_rows:
        return LoaderResult(
            dataframe=pd.DataFrame(columns=headers),
            cell_types={col: [] for col in headers},
            source_metadata={
                "filename": path.name,
                "row_count": 0,
                "column_count": n_cols,
            },
        )

    df = pd.DataFrame(inferred_rows, columns=headers, dtype=object)
    cell_types = {headers[i]: col_types[i] for i in range(n_cols)}

    source_metadata = {
        "filename": path.name,
        "row_count": len(inferred_rows),
        "column_count": n_cols,
    }

    return LoaderResult(
        dataframe=df,
        cell_types=cell_types,
        source_metadata=source_metadata,
    )
