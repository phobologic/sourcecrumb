"""TOON (Token-Oriented Object Notation) encoder."""

from __future__ import annotations

import re

from repoguide.models import RepoMap, TagKind

_NEEDS_QUOTING = re.compile(r'[,:"\\{}\[\]]')
_LOOKS_NUMERIC = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")
_KEYWORDS = frozenset({"true", "false", "null"})


def encode(repo_map: RepoMap) -> str:
    """Encode a RepoMap into TOON format.

    Args:
        repo_map: The repository map to encode.

    Returns:
        TOON-formatted string (no trailing newline).
    """
    parts: list[str] = []

    parts.append(f"repo: {_encode_value(repo_map.repo_name)}")
    parts.append(f"root: {_encode_value(repo_map.root.name)}")

    file_rows = [[str(fi.path), fi.language, f"{fi.rank:.4f}"] for fi in repo_map.files]
    parts.append(_format_tabular("files", ["path", "language", "rank"], file_rows))

    symbol_rows: list[list[str]] = []
    for fi in repo_map.files:
        for tag in fi.tags:
            if tag.kind == TagKind.DEFINITION:
                symbol_rows.append(
                    [
                        str(fi.path),
                        tag.name,
                        tag.symbol_kind.value,
                        str(tag.line),
                        tag.signature,
                    ]
                )
    parts.append(
        _format_tabular(
            "symbols",
            ["file", "name", "kind", "line", "signature"],
            symbol_rows,
        )
    )

    dep_rows = [
        [str(d.source), str(d.target), " ".join(d.symbols)]
        for d in repo_map.dependencies
    ]
    parts.append(
        _format_tabular("dependencies", ["source", "target", "symbols"], dep_rows)
    )

    return "\n".join(parts)


def _format_tabular(
    name: str,
    columns: list[str],
    rows: list[list[str]],
) -> str:
    """Format a tabular array in TOON notation.

    Args:
        name: The array field name.
        columns: Column header names.
        rows: List of row data (each row is list of strings).

    Returns:
        TOON tabular array string.
    """
    header = f"{name}[{len(rows)}]{{{','.join(columns)}}}:"
    lines = [header]
    for row in rows:
        encoded = [_encode_value(cell) for cell in row]
        lines.append(f"  {','.join(encoded)}")
    return "\n".join(lines)


def _encode_value(value: str) -> str:
    """Encode a single value, quoting if necessary per TOON rules.

    Args:
        value: The raw string value.

    Returns:
        The value, possibly double-quoted with escapes applied.
    """
    if not value:
        return '""'

    if value != value.strip():
        return _quote(value)

    if any(c in value for c in "\n\r\t"):
        return _quote(value)

    if value.lower() in _KEYWORDS:
        return _quote(value)

    if _LOOKS_NUMERIC.match(value):
        return value

    if _NEEDS_QUOTING.search(value):
        return _quote(value)

    if value.startswith("-"):
        return _quote(value)

    return value


def _quote(value: str) -> str:
    """Double-quote a string with TOON escape rules."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{escaped}"'
