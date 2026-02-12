"""Tests for the CLI entry point."""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from repoguide.cli import app

runner = CliRunner()


class TestCLI:
    """Tests for the repoguide CLI."""

    def test_map_default(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo)])
        assert result.exit_code == 0
        assert "repo:" in result.stdout
        assert "files[" in result.stdout
        assert "symbols[" in result.stdout
        assert "dependencies[" in result.stdout

    def test_map_max_files(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo), "--max-files", "2"])
        assert result.exit_code == 0
        assert "files[2]" in result.stdout

    def test_map_nonexistent_root(self, tmp_path: Path) -> None:
        result = runner.invoke(app, [str(tmp_path / "nope")])
        assert result.exit_code != 0

    def test_map_empty_repo(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("hello", encoding="utf-8")
        result = runner.invoke(app, [str(tmp_path)])
        assert result.exit_code == 1

    def test_map_language_filter(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo), "--language", "python"])
        assert result.exit_code == 0

    def test_map_unsupported_language(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo), "--language", "cobol"])
        assert result.exit_code == 1

    def test_output_contains_signatures(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo)])
        assert result.exit_code == 0
        assert "signature" in result.stdout
        # Check that a known signature appears
        assert "User" in result.stdout

    def test_output_contains_dependency(self, sample_repo: Path) -> None:
        result = runner.invoke(app, [str(sample_repo)])
        assert result.exit_code == 0
        assert "main.py" in result.stdout

    def test_parse_unicode_error_skipped(self, sample_repo: Path) -> None:
        with patch(
            "repoguide.cli.extract_tags",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad"),
        ):
            result = runner.invoke(app, [str(sample_repo)])
        assert result.exit_code == 1  # All files fail → no files parsed
        assert "Warning" in result.output

    def test_parse_programming_error_not_swallowed(self, sample_repo: Path) -> None:
        with patch(
            "repoguide.cli.extract_tags",
            side_effect=TypeError("bug"),
        ):
            result = runner.invoke(app, [str(sample_repo)])
        assert result.exit_code == 1
        assert isinstance(result.exception, TypeError)


class TestCache:
    """Tests for the --cache flag."""

    def test_cache_creates_file(self, sample_repo: Path, tmp_path: Path) -> None:
        cache_file = tmp_path / "map.cache"
        result = runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        assert result.exit_code == 0
        assert cache_file.is_file()
        assert cache_file.read_text("utf-8") == result.stdout

    def test_cache_reuses_when_fresh(self, sample_repo: Path, tmp_path: Path) -> None:
        cache_file = tmp_path / "map.cache"
        runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        first_mtime = cache_file.stat().st_mtime

        # Second run should reuse the cache (mtime unchanged).
        result = runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        assert result.exit_code == 0
        assert cache_file.stat().st_mtime == first_mtime

    def test_cache_stale_when_file_deleted(
        self, sample_repo: Path, tmp_path: Path
    ) -> None:
        cache_file = tmp_path / "map.cache"
        runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])

        # Delete a source file after cache was written.
        source = sample_repo / "models.py"
        source.unlink()

        # Should not crash - cache is treated as stale.
        result = runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        assert result.exit_code == 0

    def test_cache_invalidates_on_edit(self, sample_repo: Path, tmp_path: Path) -> None:
        cache_file = tmp_path / "map.cache"
        runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        first_mtime = cache_file.stat().st_mtime

        # Touch a source file to make it newer than the cache.
        time.sleep(0.05)
        source = sample_repo / "models.py"
        os.utime(source, None)

        result = runner.invoke(app, [str(sample_repo), "--cache", str(cache_file)])
        assert result.exit_code == 0
        assert cache_file.stat().st_mtime > first_mtime
