"""Analyzer contract and registry.

There is no abstract base class.  An analyzer is any callable matching::

    Callable[[LoaderResult], list[Finding]]

It receives a :class:`~datascope.models.LoaderResult` and returns zero or
more :class:`~datascope.models.Finding` instances.  The pipeline runner
(U9) will call each registered analyzer and merge the results.
"""

from __future__ import annotations

from typing import Callable

from datascope.models import Finding, LoaderResult

#: Type alias documenting the analyzer contract.
Analyzer = Callable[[LoaderResult], list[Finding]]
