"""Loader dispatch -- route by file extension.

No abstract base class.  The contract is simply "function that takes a
path and returns :class:`~datascope.models.LoaderResult`."
"""

from __future__ import annotations

from pathlib import Path

from datascope.models import LoaderResult


def load(path: str | Path, *, sheet: str | int = 0) -> LoaderResult:
    """Load a tabular file, dispatching by extension.

    Supported extensions:

    * ``.xlsx`` -- Excel (via openpyxl)
    * ``.csv``  -- Comma-separated values

    Parameters
    ----------
    path:
        File path.  Both ``str`` and ``Path`` are accepted.
    sheet:
        Sheet name or 0-based index (Excel only, ignored for CSV).

    Returns
    -------
    LoaderResult

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the extension is unsupported.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext == ".xlsx":
        from datascope.loaders.excel import load_excel
        return load_excel(path, sheet=sheet)

    if ext == ".csv":
        from datascope.loaders.csv_loader import load_csv
        return load_csv(path)

    raise ValueError(
        f"Unsupported file extension '{ext}'. "
        f"Supported: .xlsx, .csv"
    )
