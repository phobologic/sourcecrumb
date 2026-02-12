# repoguide

Tree-sitter repository map in TOON format for LLM consumption.

@include ../claude_code/python/CLAUDE.md

## Commands

```
uv sync                              # install deps
uv run pytest                        # run tests
uv run ruff check repoguide/ tests/  # lint
uv run ruff format repoguide/ tests/ # format
uv run repoguide .                   # run on current repo
```

## Architecture

CLI (typer) → discover files → tree-sitter parse → build dependency graph →
PageRank rank → select top files → encode to TOON → print to stdout.

Flat package layout: `repoguide/` for source, `tests/` for tests.
