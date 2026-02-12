"""Shared test fixtures for repoguide."""

from __future__ import annotations

from pathlib import Path

import pytest

from repoguide.models import (
    Dependency,
    FileInfo,
    RepoMap,
    SymbolKind,
    Tag,
    TagKind,
)


@pytest.fixture()
def sample_python_file(tmp_path: Path) -> Path:
    """Create a simple Python file with known symbols."""
    code = tmp_path / "sample.py"
    code.write_text(
        '''\
class Greeter:
    """A simple greeter."""

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


def main() -> None:
    g = Greeter()
    g.greet("world")
''',
        encoding="utf-8",
    )
    return code


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    """Create a small multi-file Python repo with cross-references."""
    (tmp_path / "models.py").write_text(
        '''\
class User:
    """A user model."""

    def __init__(self, name: str) -> None:
        self.name = name
''',
        encoding="utf-8",
    )
    (tmp_path / "utils.py").write_text(
        """\
def format_name(name: str) -> str:
    return name.strip().title()
""",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        """\
from models import User
from utils import format_name


def run() -> None:
    name = format_name("alice")
    user = User(name)
    print(user.name)
""",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def sample_file_infos() -> list[FileInfo]:
    """Pre-built FileInfo objects with known tags for graph tests."""
    main_path = Path("main.py")
    models_path = Path("models.py")
    utils_path = Path("utils.py")

    return [
        FileInfo(
            path=main_path,
            language="python",
            tags=[
                Tag(
                    name="run",
                    kind=TagKind.DEFINITION,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=5,
                    file=main_path,
                    signature="run() -> None",
                ),
                Tag(
                    name="User",
                    kind=TagKind.REFERENCE,
                    symbol_kind=SymbolKind.MODULE,
                    line=1,
                    file=main_path,
                ),
                Tag(
                    name="format_name",
                    kind=TagKind.REFERENCE,
                    symbol_kind=SymbolKind.MODULE,
                    line=2,
                    file=main_path,
                ),
                Tag(
                    name="format_name",
                    kind=TagKind.REFERENCE,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=6,
                    file=main_path,
                ),
                Tag(
                    name="User",
                    kind=TagKind.REFERENCE,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=7,
                    file=main_path,
                ),
            ],
        ),
        FileInfo(
            path=models_path,
            language="python",
            tags=[
                Tag(
                    name="User",
                    kind=TagKind.DEFINITION,
                    symbol_kind=SymbolKind.CLASS,
                    line=1,
                    file=models_path,
                    signature="User",
                ),
                Tag(
                    name="User.__init__",
                    kind=TagKind.DEFINITION,
                    symbol_kind=SymbolKind.METHOD,
                    line=4,
                    file=models_path,
                    signature="__init__(self, name: str) -> None",
                ),
            ],
        ),
        FileInfo(
            path=utils_path,
            language="python",
            tags=[
                Tag(
                    name="format_name",
                    kind=TagKind.DEFINITION,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=1,
                    file=utils_path,
                    signature="format_name(name: str) -> str",
                ),
            ],
        ),
    ]


@pytest.fixture()
def sample_repo_map(sample_file_infos: list[FileInfo]) -> RepoMap:
    """Pre-built RepoMap for encoder tests."""
    return RepoMap(
        repo_name="myproject",
        root=Path("/tmp/myproject"),
        files=sample_file_infos,
        dependencies=[
            Dependency(
                source=Path("main.py"),
                target=Path("models.py"),
                symbols=["User"],
            ),
            Dependency(
                source=Path("main.py"),
                target=Path("utils.py"),
                symbols=["format_name"],
            ),
        ],
    )
