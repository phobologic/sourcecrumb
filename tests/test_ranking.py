"""Tests for token-budget file selection."""

from __future__ import annotations

from pathlib import Path

from repoguide.models import Dependency, FileInfo, RepoMap
from repoguide.ranking import select_files


class TestSelectFiles:
    """Tests for select_files."""

    def test_limits_file_count(self) -> None:
        repo_map = RepoMap(
            repo_name="test",
            root=Path("/tmp"),
            files=[
                FileInfo(path=Path("a.py"), language="python", rank=0.5),
                FileInfo(path=Path("b.py"), language="python", rank=0.3),
                FileInfo(path=Path("c.py"), language="python", rank=0.2),
            ],
        )
        result = select_files(repo_map, max_files=2)
        assert len(result.files) == 2

    def test_no_limit_returns_all(self) -> None:
        repo_map = RepoMap(
            repo_name="test",
            root=Path("/tmp"),
            files=[
                FileInfo(path=Path("a.py"), language="python"),
                FileInfo(path=Path("b.py"), language="python"),
            ],
        )
        result = select_files(repo_map)
        assert len(result.files) == 2

    def test_filters_dependencies(self) -> None:
        repo_map = RepoMap(
            repo_name="test",
            root=Path("/tmp"),
            files=[
                FileInfo(path=Path("a.py"), language="python", rank=0.5),
                FileInfo(path=Path("b.py"), language="python", rank=0.3),
                FileInfo(path=Path("c.py"), language="python", rank=0.2),
            ],
            dependencies=[
                Dependency(source=Path("a.py"), target=Path("b.py"), symbols=["foo"]),
                Dependency(source=Path("a.py"), target=Path("c.py"), symbols=["bar"]),
            ],
        )
        result = select_files(repo_map, max_files=2)
        # c.py is excluded, so a->c dependency should be filtered out
        assert len(result.dependencies) == 1
        assert result.dependencies[0].target == Path("b.py")

    def test_max_files_larger_than_total(self) -> None:
        repo_map = RepoMap(
            repo_name="test",
            root=Path("/tmp"),
            files=[FileInfo(path=Path("a.py"), language="python")],
        )
        result = select_files(repo_map, max_files=100)
        assert len(result.files) == 1
