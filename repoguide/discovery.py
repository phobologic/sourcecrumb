"""File discovery with gitignore support."""

from __future__ import annotations

import os
from pathlib import Path

import pathspec

from repoguide.languages import language_for_extension

SKIP_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        "node_modules",
        ".git",
        ".hg",
        ".svn",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "egg-info",
    }
)


def discover_files(
    root: Path,
    *,
    extra_ignores: list[str] | None = None,
    language_filter: str | None = None,
) -> list[tuple[Path, str]]:
    """Walk root and return (relative_path, language_name) for parseable files.

    Args:
        root: Repository root directory.
        extra_ignores: Additional gitignore-style patterns to exclude.
        language_filter: If set, only return files matching this language name.

    Returns:
        List of (relative_path, language_name) tuples, sorted by path.
    """
    gitignore = _load_gitignore(root)

    extra_spec = None
    if extra_ignores:
        extra_spec = pathspec.PathSpec.from_lines("gitignore", extra_ignores)

    results: list[tuple[Path, str]] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune skip dirs and hidden dirs in-place to prevent descent
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )

        rel_dir = Path(dirpath).relative_to(root)

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue

            full_path = Path(dirpath) / fname
            if full_path.is_symlink():
                continue

            rel = rel_dir / fname

            if gitignore.match_file(str(rel)):
                continue

            if extra_spec and extra_spec.match_file(str(rel)):
                continue

            lang = language_for_extension(Path(fname).suffix)
            if lang is None:
                continue

            if language_filter and lang.name != language_filter:
                continue

            results.append((rel, lang.name))

    results.sort()
    return results


def _load_gitignore(root: Path) -> pathspec.PathSpec:
    """Load .gitignore from root, returning a PathSpec matcher."""
    gitignore_path = root / ".gitignore"
    if gitignore_path.is_file():
        lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        return pathspec.PathSpec.from_lines("gitignore", lines)
    return pathspec.PathSpec.from_lines("gitignore", [])
