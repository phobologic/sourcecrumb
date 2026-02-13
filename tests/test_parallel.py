"""Tests for parallel file parsing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from sourcecrumb.parallel import (
    _parse_file_worker,
    parse_files_parallel,
)


class TestParseFileWorker:
    """Unit tests for the worker function."""

    def test_successful_parse(self, sample_repo: Path) -> None:
        _rel_path, _lang_name, tags, warning = _parse_file_worker(
            sample_repo, Path("models.py"), "python"
        )
        assert tags is not None
        assert warning is None
        assert len(tags) > 0

    def test_missing_file(self, sample_repo: Path) -> None:
        _rel_path, _lang_name, tags, warning = _parse_file_worker(
            sample_repo, Path("nonexistent.py"), "python"
        )
        assert tags is None
        assert warning is not None

    def test_unicode_decode_error(self, sample_repo: Path) -> None:
        with patch(
            "sourcecrumb.parallel.extract_tags",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad"),
        ):
            _rel_path, _lang_name, tags, warning = _parse_file_worker(
                sample_repo, Path("models.py"), "python"
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
