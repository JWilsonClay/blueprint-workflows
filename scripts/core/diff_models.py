"""
diff_models.py — Data models for the Diff Review Node
=====================================================
Extracted from refactor_diff.py during SoC decomposition.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING  = "WARNING"
    INFO     = "INFO"


@dataclass
class Deviation:
    severity: Severity
    category: str
    path: str
    message: str
    suggestion: str = ""


@dataclass
class DiffReport:
    phase: str
    project_root: Path
    deviations: list = field(default_factory=list)

    def add(self, severity: Severity, category: str, path: str,
            message: str, suggestion: str = "") -> None:
        self.deviations.append(Deviation(severity, category, path, message, suggestion))

    @property
    def criticals(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.CRITICAL]

    @property
    def warnings(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.WARNING]

    @property
    def infos(self) -> list:
        return [d for d in self.deviations if d.severity == Severity.INFO]

    @property
    def is_clean(self) -> bool:
        return len(self.criticals) == 0
