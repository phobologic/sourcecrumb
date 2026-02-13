"""Parallel file parsing for the --fast experimental flag."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import typer

from sourcecrumb.languages import LANGUAGES
from sourcecrumb.models import FileInfo, Tag
from sourcecrumb.parsing import extract_tags

_DEFAULT_MAX_FILE_SIZE = 1_000_000  # 1 MB


def _parse_file_worker(
    root: Path,
    rel_path: Path,
    lang_name: str,
    max_size_bytes: int,
) -> tuple[Path, str, list[Tag] | None, str | None]:
    """Parse a single file, returning tags or a warning message.

    Module-level function required for ProcessPoolExecutor pickling.

    Args:
        root: Repository root directory.
        rel_path: Relative path to the file.
        lang_name: Language name key in LANGUAGES.
        max_size_bytes: Skip files larger than this.

    Returns:
        Tuple of (rel_path, lang_name, tags_or_None, warning_or_None).
    """
    abs_path = root / rel_path
    try:
        size = abs_path.stat().st_size
        if size > max_size_bytes:
            return (rel_path, lang_name, None, f"skipped (>{max_size_bytes} bytes)")
        lang_config = LANGUAGES[lang_name]
        tags = extract_tags(abs_path, lang_config)
    except (OSError, UnicodeDecodeError) as exc:
        return (rel_path, lang_name, None, str(exc))
    return (rel_path, lang_name, tags, None)


def parse_files_parallel(
    root: Path,
    files: list[tuple[Path, str]],
    *,
    max_size_bytes: int | None = None,
    max_workers: int | None = None,
) -> list[FileInfo]:
    """Parse files in parallel using ProcessPoolExecutor.

    Args:
        root: Repository root directory.
        files: List of (rel_path, lang_name) tuples from discovery.
        max_size_bytes: Skip files larger than this (default 1MB).
        max_workers: Maximum number of worker processes.

    Returns:
        List of FileInfo for successfully parsed files.
    """
    if max_size_bytes is None:
        max_size_bytes = _DEFAULT_MAX_FILE_SIZE
    if max_workers is None:
        max_workers = min(os.cpu_count() or 1, len(files))

    file_infos: list[FileInfo] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _parse_file_worker, root, rel_path, lang_name, max_size_bytes
            ): rel_path
            for rel_path, lang_name in files
        }
        for future in as_completed(futures):
            rel_path, lang_name, tags, warning = future.result()
            if warning:
                typer.echo(f"Warning: {rel_path}: {warning}", err=True)
                continue
            file_infos.append(FileInfo(path=rel_path, language=lang_name, tags=tags))

    file_infos.sort(key=lambda fi: fi.path)
    return file_infos
