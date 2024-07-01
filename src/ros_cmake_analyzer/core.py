from __future__ import annotations

import enum
import typing as t
from dataclasses import dataclass


class SourceLanguage(enum.Enum):
    CXX = "cxx"
    PYTHON = "python"


@dataclass(frozen=True)
class CMakeTarget:
    name: str
    language: SourceLanguage
    sources: set[str]
    restrict_to_paths: set[str]
    cmakelists_file: str
    cmakelists_line: int

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "name": self.name,
            "language": self.language.value,
            "sources": list(self.sources),
            "path_restrictions": list(self.restrict_to_paths),
            "cmakelists_file": self.cmakelists_file,
            "cmakelists_line": self.cmakelists_line,
        }

    @classmethod
    def from_dict(cls, info: dict[str, t.Any]) -> CMakeTarget:
        return CMakeTarget(
            info["name"],
            SourceLanguage(info["language"]),
            set(info["sources"]),
            set(info["path_restrictions"]),
            info["cmakelists_file"],
            info["cmakelists_line"],
        )
