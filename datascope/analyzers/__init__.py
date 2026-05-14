"""datascope.analyzers -- detectors that produce Finding objects."""

from datascope.analyzers.type_consistency import analyze_type_consistency
from datascope.analyzers.sentinel import analyze_sentinels

__all__ = ["analyze_type_consistency", "analyze_sentinels"]
