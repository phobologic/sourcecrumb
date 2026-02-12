"""Tests for file discovery."""

from __future__ import annotations

from pathlib import Path

from repoguide.discovery import discover_files


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
