"""Tests for parallel file parsing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from sourcecrumb.parallel import (
    _DEFAULT_MAX_FILE_SIZE,
    _parse_file_worker,
    parse_files_parallel,
)


class TestParseFileWorker:
    """Unit tests for the worker function."""

    def test_successful_parse(self, sample_repo: Path) -> None:
        _rel_path, _lang_name, tags, warning = _parse_file_worker(
            sample_repo, Path("models.py"), "python", _DEFAULT_MAX_FILE_SIZE
        )
        assert tags is not None
        assert warning is None
        assert len(tags) > 0

    def test_file_over_size_limit(self, sample_repo: Path) -> None:
        _rel_path, _lang_name, tags, warning = _parse_file_worker(
            sample_repo, Path("models.py"), "python", 1
        )
        assert tags is None
        assert warning is not None
        assert "skipped" in warning

    def test_missing_file(self, sample_repo: Path) -> None:
        _rel_path, _lang_name, tags, warning = _parse_file_worker(
            sample_repo, Path("nonexistent.py"), "python", _DEFAULT_MAX_FILE_SIZE
        )
        assert tags is None
        assert warning is not None

    def test_unicode_decode_error(self, sample_repo: Path) -> None:
        with patch(
            "sourcecrumb.parallel.extract_tags",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad"),
        ):
            _rel_path, _lang_name, tags, warning = _parse_file_worker(
                sample_repo, Path("models.py"), "python", _DEFAULT_MAX_FILE_SIZE
            )
        assert tags is None
        assert warning is not None


class TestParseFilesParallel:
    """Integration tests for parallel parsing."""

    def test_parses_sample_repo(self, sample_repo: Path) -> None:
        files = [
            (Path("models.py"), "python"),
            (Path("utils.py"), "python"),
            (Path("main.py"), "python"),
        ]
        result = parse_files_parallel(sample_repo, files)
        assert len(result) == 3
        paths = {fi.path for fi in result}
        assert paths == {Path("models.py"), Path("utils.py"), Path("main.py")}

    def test_single_worker_fallback(self, sample_repo: Path) -> None:
        files = [
            (Path("models.py"), "python"),
            (Path("utils.py"), "python"),
        ]
        result = parse_files_parallel(sample_repo, files, max_workers=1)
        assert len(result) == 2

    def test_file_size_filtering(self, tmp_path: Path) -> None:
        # Small file passes, large file skipped.
        (tmp_path / "small.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "large.py").write_text("y = 2\n" * 1000, encoding="utf-8")
        files = [
            (Path("small.py"), "python"),
            (Path("large.py"), "python"),
        ]
        # Set max_size to something between the two file sizes.
        small_size = (tmp_path / "small.py").stat().st_size
        large_size = (tmp_path / "large.py").stat().st_size
        limit = (small_size + large_size) // 2
        result = parse_files_parallel(
            tmp_path, files, max_size_bytes=limit, max_workers=1
        )
        assert len(result) == 1
        assert result[0].path == Path("small.py")
