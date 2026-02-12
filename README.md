# repoguide

Tree-sitter repository map in TOON format for LLM consumption.

## What it does

repoguide parses a codebase with tree-sitter, extracts symbols (classes, functions, methods, imports), builds a file-to-file dependency graph, and ranks files by PageRank. The output is a compact TOON-formatted map designed to fit in an LLM context window.

The goal: give an LLM agent a high-level map of a codebase so it can explore more effectively — knowing which files matter most, what symbols they define, and how they depend on each other.

## Installation

Requires Python >= 3.13.

```
git clone <repo-url>
cd repoguide
uv sync
```

## Usage

```
repoguide [ROOT] [OPTIONS]
```

| Option | Description |
|---|---|
| `ROOT` | Repository root directory (default: `.`) |
| `--max-files`, `-n` | Limit output to top N files by PageRank (min: 1) |
| `--language`, `-l` | Restrict to a specific language (e.g., `python`) |
| `--cache` | Cache file path; reuses if newer than all source files |

### Example

```
$ repoguide . -n 3
repo: repoguide
root: repoguide
files[3]{path,language,rank}:
  repoguide/models.py,python,0.2615
  repoguide/languages.py,python,0.1155
  repoguide/discovery.py,python,0.0590
symbols[17]{file,name,kind,line,signature}:
  repoguide/models.py,TagKind,class,10,TagKind(enum.Enum)
  repoguide/models.py,SymbolKind,class,17,SymbolKind(enum.Enum)
  repoguide/models.py,Tag,class,27,Tag
  repoguide/models.py,FileInfo,class,39,FileInfo
  ...
dependencies[1]{source,target,symbols}:
  repoguide/discovery.py,repoguide/languages.py,language_for_extension
```

## Claude Code integration

The primary use case is running repoguide as a Claude Code hook so every subagent automatically gets a repo map injected into its context.

Add this to `.claude/settings.json`:

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "repoguide \"$CLAUDE_PROJECT_DIR\" --cache \"$CLAUDE_PROJECT_DIR/.cache/repoguide.toon\""
          }
        ]
      }
    ]
  }
}
```

The `SubagentStart` hook fires when any subagent launches. repoguide's stdout is injected into the subagent's context, giving it an instant overview of the codebase.

`--cache` avoids re-parsing on every agent launch — the cache file is reused as long as no source files have changed. Add `.cache/` to your `.gitignore`.

## TOON format

The output uses TOON (Text Object Oriented Notation), a compact format designed for LLM consumption:

- **Scalar fields** — `key: value`
- **Tabular arrays** — `name[count]{col1,col2,...}:` followed by indented CSV rows
- **Quoting** — values containing special characters are double-quoted; numbers and plain strings are bare

## How it works

1. **Discover files** — uses `git ls-files` when available, falls back to `.gitignore`-based filtering
2. **Parse with tree-sitter** — extracts classes, functions, methods, and imports from each file
3. **Build dependency graph** — creates file-to-file edges based on shared symbols (imports that resolve to definitions in other files)
4. **Rank with PageRank** — scores files by importance in the dependency graph
5. **Select top N** — when `--max-files` is set, keeps only the highest-ranked files
6. **Encode to TOON** — serializes the repo map into the compact output format

## Supported languages

Python. Extensible by adding a `.scm` query file to `repoguide/queries/` and registering the language in `repoguide/languages.py`.

## Development

```
uv run pytest                        # run tests
uv run ruff check repoguide/ tests/  # lint
uv run ruff format repoguide/ tests/ # format
```
