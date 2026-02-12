"""Core data structures for repoguide."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path


class TagKind(enum.Enum):
    """Whether a tag is a definition or a reference."""

    DEFINITION = "def"
    REFERENCE = "ref"


class SymbolKind(enum.Enum):
    """The syntactic kind of a symbol."""

    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    MODULE = "module"


@dataclass(frozen=True)
class Tag:
    """A single symbol occurrence extracted from source code."""

    name: str
    kind: TagKind
    symbol_kind: SymbolKind
    line: int
    file: Path
    signature: str = ""


@dataclass
class FileInfo:
    """Metadata and extracted tags for a single source file."""

    path: Path
    language: str
    tags: list[Tag] = field(default_factory=list)
    rank: float = 0.0


@dataclass
class Dependency:
    """An edge in the dependency graph: source references symbols defined in target."""

    source: Path
    target: Path
    symbols: list[str] = field(default_factory=list)


@dataclass
class RepoMap:
    """The complete analyzed repository map, ready for serialization."""

    repo_name: str
    root: Path
    files: list[FileInfo] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
