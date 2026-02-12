"""Tests for file discovery."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from repoguide.discovery import _git_ls_files, discover_files


class TestDiscoverFiles:
    """Tests for discover_files."""

    def test_finds_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        (tmp_path / "lib.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert Path("app.py") in paths
        assert Path("lib.py") in paths

    def test_skips_hidden_dirs(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        assert len(result) == 0

    def test_skips_common_dirs(self, tmp_path: Path) -> None:
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("pass", encoding="utf-8")
        node_mods = tmp_path / "node_modules"
        node_mods.mkdir()
        (node_mods / "index.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        assert len(result) == 0

    def test_respects_gitignore(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
        (tmp_path / "ignored.py").write_text("pass", encoding="utf-8")
        (tmp_path / "kept.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert Path("ignored.py") not in paths
        assert Path("kept.py") in paths

    def test_returns_relative_paths(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        assert result[0][0] == Path("app.py")
        assert not result[0][0].is_absolute()

    def test_returns_language_name(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        assert result[0][1] == "python"

    def test_skips_unsupported_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "data.csv").write_text("a,b,c", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
        result = discover_files(tmp_path)
        assert len(result) == 0

    def test_extra_ignores(self, tmp_path: Path) -> None:
        (tmp_path / "gen.py").write_text("pass", encoding="utf-8")
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path, extra_ignores=["gen.py"])
        paths = [r[0] for r in result]
        assert Path("gen.py") not in paths
        assert Path("app.py") in paths

    def test_language_filter(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path, language_filter="python")
        assert len(result) == 1
        result_none = discover_files(tmp_path, language_filter="rust")
        assert len(result_none) == 0

    def test_sorted_by_path(self, tmp_path: Path) -> None:
        (tmp_path / "z.py").write_text("pass", encoding="utf-8")
        (tmp_path / "a.py").write_text("pass", encoding="utf-8")
        (tmp_path / "m.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert paths == sorted(paths)

    def test_skips_symlinked_files(self, tmp_path: Path) -> None:
        (tmp_path / "real.py").write_text("pass", encoding="utf-8")
        (tmp_path / "link.py").symlink_to(tmp_path / "real.py")
        result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert Path("real.py") in paths
        assert Path("link.py") not in paths

    def test_nested_directories(self, tmp_path: Path) -> None:
        sub = tmp_path / "pkg"
        sub.mkdir()
        (sub / "mod.py").write_text("pass", encoding="utf-8")
        result = discover_files(tmp_path)
        assert result[0][0] == Path("pkg/mod.py")


class TestGitLsFiles:
    """Tests for _git_ls_files."""

    def test_returns_none_without_git_dir(self, tmp_path: Path) -> None:
        assert _git_ls_files(tmp_path) is None

    def test_returns_none_on_command_error(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        with patch(
            "repoguide.discovery.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], returncode=128, stdout="", stderr=""
            ),
        ):
            assert _git_ls_files(tmp_path) is None

    def test_returns_none_on_timeout(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        with patch(
            "repoguide.discovery.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=[], timeout=10),
        ):
            assert _git_ls_files(tmp_path) is None

    def test_returns_none_on_missing_git_binary(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        with patch(
            "repoguide.discovery.subprocess.run",
            side_effect=FileNotFoundError("git"),
        ):
            assert _git_ls_files(tmp_path) is None

    def test_returns_file_set(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        with patch(
            "repoguide.discovery.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], returncode=0, stdout="a.py\npkg/b.py\n", stderr=""
            ),
        ):
            result = _git_ls_files(tmp_path)
            assert result == {"a.py", "pkg/b.py"}


class TestGitIgnoreIntegration:
    """Tests for gitignore integration via git ls-files."""

    def test_subdirectory_gitignore_honored(self, tmp_path: Path) -> None:
        """Files excluded by subdirectory .gitignore are filtered out."""
        (tmp_path / "kept.py").write_text("pass", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "visible.py").write_text("pass", encoding="utf-8")
        (sub / "hidden.py").write_text("pass", encoding="utf-8")
        # Mock git ls-files to exclude sub/hidden.py
        with patch(
            "repoguide.discovery._git_ls_files",
            return_value={"kept.py", "sub/visible.py"},
        ):
            result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert Path("kept.py") in paths
        assert Path("sub/visible.py") in paths
        assert Path("sub/hidden.py") not in paths

    def test_fallback_when_git_unavailable(self, tmp_path: Path) -> None:
        """Falls back to root .gitignore parsing when git ls-files fails."""
        (tmp_path / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
        (tmp_path / "ignored.py").write_text("pass", encoding="utf-8")
        (tmp_path / "kept.py").write_text("pass", encoding="utf-8")
        # No .git dir → _git_ls_files returns None → pathspec fallback
        result = discover_files(tmp_path)
        paths = [r[0] for r in result]
        assert Path("ignored.py") not in paths
        assert Path("kept.py") in paths

    def test_extra_ignores_with_git_ls_files(self, tmp_path: Path) -> None:
        """extra_ignores still applies when git ls-files is used."""
        (tmp_path / "gen.py").write_text("pass", encoding="utf-8")
        (tmp_path / "app.py").write_text("pass", encoding="utf-8")
        with patch(
            "repoguide.discovery._git_ls_files",
            return_value={"gen.py", "app.py"},
        ):
            result = discover_files(tmp_path, extra_ignores=["gen.py"])
        paths = [r[0] for r in result]
        assert Path("gen.py") not in paths
        assert Path("app.py") in paths
