"""Core data structures for datascope.

Every detector produces :class:`Finding` instances.  Downstream consumers
(severity classifier, NL composer, report writer) read and enrich them.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(enum.IntEnum):
    """Finding severity, ordered so that ``CRITICAL > WARNING > INFO``.

    Using IntEnum gives free comparison operators and sort support (R12).
    Higher numeric value == higher severity.
    """

    INFO = 1
    WARNING = 2
    CRITICAL = 3


class FindingType(enum.Enum):
    """The category of data-quality issue a detector found."""

    TYPE_INCONSISTENCY = "type_inconsistency"
    SENTINEL_VALUE = "sentinel_value"
    FORMAT_INCONSISTENCY = "format_inconsistency"
    CARDINALITY_ANOMALY = "cardinality_anomaly"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single data-quality finding produced by a detector.

    Detectors fill ``field_name``, ``finding_type``, and ``evidence``.
    Later pipeline stages fill the remaining fields:

    * **severity classifier** sets ``severity``.
    * **NL composer** sets ``assumption``, ``reality``, ``impact``,
      ``fix_recommendation``, and ``prevention_rule``.
    """

    field_name: str
    finding_type: FindingType
    evidence: dict = field(default_factory=dict)

    # Filled by severity classifier
    severity: Severity | None = None

    # Filled by NL composer
    assumption: str | None = None
    reality: str | None = None
    impact: str | None = None
    fix_recommendation: str | None = None
    prevention_rule: str | None = None


@dataclass
class LoaderResult:
    """What the loader hands to the profiler and detectors.

    ``cell_types`` carries per-cell Python types *separate* from the DataFrame
    so that detectors can reason about mixed-type columns without re-scanning.
    """

    dataframe: pd.DataFrame
    cell_types: dict[str, list[type]] = field(default_factory=dict)
    source_metadata: dict = field(default_factory=dict)


@dataclass
class FieldProfile:
    """Per-column profile produced by the profiler stage."""

    name: str
    completeness: float
    unique_count: int
    total_count: int
    inferred_type: str
    type_breakdown: dict[str, int] = field(default_factory=dict)
