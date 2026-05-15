"""Parquet loader -- maps Arrow schema types to Python types for cell_types.

Requires pyarrow, which is an optional dependency:
    pip install datascope-dq[parquet]

Returns a :class:`~datascope.models.LoaderResult` identical in shape to
the Excel and CSV loaders.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from datascope.models import LoaderResult

_ARROW_TYPE_MAP = {
    "int8": int,
    "int16": int,
    "int32": int,
    "int64": int,
    "uint8": int,
    "uint16": int,
    "uint32": int,
    "uint64": int,
    "float16": float,
    "float32": float,
    "float64": float,
    "double": float,
    "bool": bool,
    "string": str,
    "large_string": str,
    "utf8": str,
    "large_utf8": str,
    "binary": bytes,
    "large_binary": bytes,
}


def _arrow_type_to_python(arrow_type_str: str) -> type:
    """Map an Arrow type string to a Python type."""
    base = arrow_type_str.split("[")[0].strip()
    if base in _ARROW_TYPE_MAP:
        return _ARROW_TYPE_MAP[base]
    if base.startswith("timestamp") or base.startswith("date"):
        from datetime import datetime
        return datetime
    if base.startswith("decimal"):
        return float
    return str


def load_parquet(path: Path) -> LoaderResult:
    """Read a Parquet file with schema-based type mapping.

    Parameters
    ----------
    path:
        Path to the ``.parquet`` file.

    Returns
    -------
    LoaderResult
        DataFrame with original dtypes, per-column ``cell_types``
        derived from the Arrow schema, and source metadata.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError(
            "Parquet support requires pyarrow. "
            "Install it with: pip install datascope-dq[parquet]"
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")

    table = pq.read_table(path)
    schema = table.schema
    df = table.to_pandas()

    n_rows = len(df)
    cell_types: dict[str, list[type]] = {}

    for field in schema:
        col_name = field.name
        py_type = _arrow_type_to_python(str(field.type))

        col_types: list[type] = []
        if col_name in df.columns:
            for val in df[col_name]:
                if pd.isna(val) if not isinstance(val, (list, dict)) else False:
                    col_types.append(type(None))
                else:
                    col_types.append(py_type)
        cell_types[col_name] = col_types

    source_metadata = {
        "filename": path.name,
        "row_count": n_rows,
        "column_count": len(df.columns),
    }

    return LoaderResult(
        dataframe=df,
        cell_types=cell_types,
        source_metadata=source_metadata,
    )
