# sourcecrumb

Tree-sitter repository map in TOON format for LLM consumption.

@include ../claude_code/python/CLAUDE.md

## Commands

```
uv sync                                  # install deps
uv run pytest                            # run tests
uv run ruff check sourcecrumb/ tests/    # lint
uv run ruff format sourcecrumb/ tests/   # format
uv run scrumb .                          # run on current repo
```

## Architecture

CLI (typer) → discover files → tree-sitter parse → build dependency graph →
PageRank rank → select top files → encode to TOON → print to stdout.

Flat package layout: `sourcecrumb/` for source, `tests/` for tests.
