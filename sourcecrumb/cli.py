"""CLI entry point for sourcecrumb."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sourcecrumb.discovery import discover_files
from sourcecrumb.graph import build_graph, rank_files
from sourcecrumb.languages import LANGUAGES
from sourcecrumb.models import FileInfo, RepoMap
from sourcecrumb.parallel import _DEFAULT_MAX_FILE_SIZE
from sourcecrumb.parsing import extract_tags
from sourcecrumb.ranking import select_files
from sourcecrumb.toon import encode


def _cache_is_fresh(cache: Path, root: Path, files: list[tuple[Path, str]]) -> bool:
    """Check if cache file exists and is newer than all discovered source files."""
    if not cache.is_file():
        return False
    cache_mtime = cache.stat().st_mtime
    try:
        return all((root / rel).stat().st_mtime < cache_mtime for rel, _ in files)
    except OSError:
        return False


def _filter_by_size(
    root: Path, files: list[tuple[Path, str]], max_size_bytes: int
) -> list[tuple[Path, str]]:
    """Filter out files exceeding the size limit.

    Args:
        root: Repository root directory.
        files: List of (rel_path, lang_name) tuples.
        max_size_bytes: Skip files larger than this.

    Returns:
        Filtered list with oversized files removed.
    """
    kept: list[tuple[Path, str]] = []
    for rel_path, lang_name in files:
        try:
            size = (root / rel_path).stat().st_size
        except OSError:
            kept.append((rel_path, lang_name))
            continue
        if size > max_size_bytes:
            typer.echo(
                f"Warning: {rel_path}: skipped (>{max_size_bytes} bytes)", err=True
            )
            continue
        kept.append((rel_path, lang_name))
    return kept


def _parse_files_sequential(
    root: Path, files: list[tuple[Path, str]]
) -> list[FileInfo]:
    """Parse files sequentially, skipping files that fail to parse."""
    file_infos: list[FileInfo] = []
    for rel_path, lang_name in files:
        abs_path = root / rel_path
        lang_config = LANGUAGES[lang_name]
        try:
            tags = extract_tags(abs_path, lang_config)
        except (OSError, UnicodeDecodeError) as exc:
            typer.echo(f"Warning: failed to parse {rel_path}: {exc}", err=True)
            continue
        file_infos.append(FileInfo(path=rel_path, language=lang_name, tags=tags))
    return file_infos


app = typer.Typer(
    name="sourcecrumb",
    help="Generate a tree-sitter repository map in TOON format.",
    no_args_is_help=False,
)


@app.command()
def main(
    root: Annotated[
        Path,
        typer.Argument(
            help="Repository root directory.",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = Path("."),
    max_files: Annotated[
        int | None,
        typer.Option(
            "--max-files",
            "-n",
            min=1,
            help="Maximum number of files to include in output.",
        ),
    ] = None,
    language: Annotated[
        str | None,
        typer.Option(
            "--language",
            "-l",
            help="Restrict to a specific language (e.g., python).",
        ),
    ] = None,
    cache: Annotated[
        Path | None,
        typer.Option(
            "--cache", help="Cache file; reuse if newer than all source files."
        ),
    ] = None,
    max_file_size: Annotated[
        int,
        typer.Option(
            "--max-file-size",
            min=1,
            help="Skip files larger than this many bytes (default: 1MB).",
        ),
    ] = _DEFAULT_MAX_FILE_SIZE,
    fast: Annotated[
        bool,
        typer.Option(
            "--fast",
            help="Experimental: parse files in parallel for faster processing.",
        ),
    ] = False,
) -> None:
    """Generate a repository map and print it to stdout."""
    if language and language not in LANGUAGES:
        typer.echo(
            f"Error: unsupported language '{language}'. "
            f"Supported: {', '.join(LANGUAGES)}",
            err=True,
        )
        raise typer.Exit(1)

    files = discover_files(root, language_filter=language)
    if not files:
        typer.echo("No parseable files found.", err=True)
        raise typer.Exit(1)

    if cache and _cache_is_fresh(cache, root, files):
        typer.echo(cache.read_text("utf-8"), nl=False)
        return

    files = _filter_by_size(root, files, max_file_size)
    if not files:
        typer.echo("No parseable files found (all exceeded size limit).", err=True)
        raise typer.Exit(1)

    if fast:
        from sourcecrumb.parallel import parse_files_parallel

        file_infos = parse_files_parallel(root, files)
    else:
        file_infos = _parse_files_sequential(root, files)

    if not file_infos:
        typer.echo("No files could be parsed.", err=True)
        raise typer.Exit(1)

    graph, dependencies = build_graph(file_infos)
    rank_files(graph, file_infos)

    repo_map = RepoMap(
        repo_name=root.name,
        root=root,
        files=file_infos,
        dependencies=dependencies,
    )

    repo_map = select_files(repo_map, max_files=max_files)

    output = encode(repo_map)
    if cache:
        cache.write_text(output + "\n", "utf-8")
    typer.echo(output)
