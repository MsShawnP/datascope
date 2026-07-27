"""Loader dispatch -- route by file extension.

No abstract base class.  The contract is simply "function that takes a
path and returns :class:`~datascope.models.LoaderResult`."
"""

from __future__ import annotations

from pathlib import Path

from datascope.models import LoaderResult


def dedupe_headers(headers: list[str]) -> list[str]:
    """Disambiguate repeated column names the way pandas' readers do.

    The first occurrence keeps its name; later duplicates get a numeric
    suffix (``amount`` -> ``amount``, ``amount.1``, ``amount.2``). Without
    this, two columns sharing a header collapse to one ``cell_types`` entry
    while the DataFrame keeps both, so ``df[name]`` returns a same-named
    DataFrame instead of a Series and per-column analyzers crash (and the
    crash is silently swallowed by the CLI). Suffixes that would collide
    with an existing header are skipped.
    """
    seen: dict[str, int] = {}
    taken = set(headers)
    out: list[str] = []
    for h in headers:
        if h not in seen:
            seen[h] = 0
            out.append(h)
            continue
        seen[h] += 1
        candidate = f"{h}.{seen[h]}"
        while candidate in taken:
            seen[h] += 1
            candidate = f"{h}.{seen[h]}"
        taken.add(candidate)
        out.append(candidate)
    return out


def load(path: str | Path, *, sheet: str | int = 0) -> LoaderResult:
    """Load a tabular file, dispatching by extension.

    Supported extensions:

    * ``.xlsx``    -- Excel (via openpyxl)
    * ``.csv``     -- Comma-separated values
    * ``.parquet`` -- Apache Parquet (via optional pyarrow)

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

    if ext == ".parquet":
        from datascope.loaders.parquet import load_parquet
        return load_parquet(path)

    raise ValueError(
        f"Unsupported file extension '{ext}'. "
        f"Supported: .xlsx, .csv, .parquet"
    )
