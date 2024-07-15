from __future__ import annotations

import enum
import typing as t
from dataclasses import dataclass

if t.TYPE_CHECKING:
    from pathlib import Path

DUMMY_VALUE = "__dummy_property_value__"  # A dummy value used as a stand in for properties we don't need


class SourceLanguage(enum.Enum):
    CXX = "cxx"
    PYTHON = "python"


@dataclass
class FileInformation:
    path: str
    cmake_file: Path
    cmake_line_no: int


@dataclass
class CommandInformation:
    command: list[str]
    cmake_file: Path
    cmake_line_no: int


@dataclass(frozen=True)
class CMakeTarget:
    name: str
    language: SourceLanguage
    sources: set[Path]
    includes: list[Path]
    restrict_to_paths: set[Path]
    cmakelists_file: str
    cmakelists_line: int

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "name": self.name,
            "language": self.language.value,
            "sources": list(self.sources),
            "includes": self.includes,
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
            list(info["includes"]),
            set(info["path_restrictions"]),
            info["cmakelists_file"],
            info["cmakelists_line"],
        )


@dataclass(frozen=True)
class CMakeBinaryTarget(CMakeTarget):
    _entrypoint: str | None = None

    @property
    def entrypoint(self) -> str | None:
        if self.language == SourceLanguage.CXX:
            return "main"
        return None

    def to_dict(self) -> dict[str, t.Any]:
        d = super().to_dict()
        if self.entrypoint:
            d["entrypoint"] = self.entrypoint
        return d

    @classmethod
    def from_dict(cls, info: dict[str, t.Any]) -> CMakeBinaryTarget:
        return CMakeBinaryTarget(info["name"],
                                 SourceLanguage(info["language"]),
                                 set(info["sources"]),
                                 list(info["includes"]),
                                 set(info["path_restrictions"]),
                                 info["cmakelists_file"],
                                 info["cmakelists_line"],
                                 info.get("entrypoint", None))


@dataclass(frozen=True)
class CMakeLibraryTarget(CMakeBinaryTarget):
    _entrypoint: str


@dataclass(frozen=True)
class CMakeInfo:
    """Summarizes the source generating parts of a CMakeFile.

    Attributes
    ----------
    cmake_file: Path
        The path to the CMakeLists.txt file that contains the information
    targets: Dict[str, CMakeTarget]
        A mapping of nodes or nodelets to the CMakeTarget that contains the source code for them.
    generated_sources: Collection[str]
        A collection of sources that were generated by targets in the CMakeLists file.
    unresolved_files: set[FileInformation]
        Files that were unresolved, along with their location
    unprocessed_commands: list[CommandInformation]
        Commands that were not processed

    """

    cmake_file: Path
    targets: dict[str, CMakeTarget]
    generated_sources: t.Collection[str]
    unresolved_files: set[FileInformation]
    unprocessed_commands: list[CommandInformation]


@dataclass(frozen=True)
class NodeletLibrary:
    """Represents a piece of information found in the nodelet_plygin.xml file.

    path: str
        The path to the library containing the nodelet
    name: str
        The class name of the main entrypoint for the nodelet
    tupe_: str
        The type of the class
    """

    path: str
    name: str
    type_: str

    @property
    def entrypoint(self) -> str:
        return self.type_ + "::onInit"


@dataclass(frozen=True)
class IncompleteCMakeLibraryTarget(CMakeTarget):

    def complete(self, entrypoint: str) -> CMakeLibraryTarget:
        return CMakeLibraryTarget(name=self.name,
                                  language=self.language,
                                  sources=self.sources,
                                  includes=self.includes,
                                  restrict_to_paths=self.restrict_to_paths,
                                  cmakelists_file=self.cmakelists_file,
                                  cmakelists_line=self.cmakelists_line,
                                  _entrypoint=entrypoint)
