"""Tests for the TOON encoder."""

from __future__ import annotations

from pathlib import Path

from repoguide.models import FileInfo, RepoMap, SymbolKind, Tag, TagKind
from repoguide.toon import _encode_value, encode


class TestEncodeValue:
    """Tests for _encode_value."""

    def test_plain_string_unquoted(self) -> None:
        assert _encode_value("hello") == "hello"

    def test_string_with_comma_quoted(self) -> None:
        assert _encode_value("a,b") == '"a,b"'

    def test_string_with_colon_quoted(self) -> None:
        assert _encode_value("a:b") == '"a:b"'

    def test_number_unquoted(self) -> None:
        assert _encode_value("42") == "42"
        assert _encode_value("3.14") == "3.14"

    def test_empty_string_quoted(self) -> None:
        assert _encode_value("") == '""'

    def test_boolean_keywords_quoted(self) -> None:
        assert _encode_value("true") == '"true"'
        assert _encode_value("false") == '"false"'
        assert _encode_value("null") == '"null"'

    def test_leading_whitespace_quoted(self) -> None:
        assert _encode_value(" hello") == '" hello"'

    def test_string_with_quotes_escaped(self) -> None:
        assert _encode_value('say "hi"') == '"say \\"hi\\""'

    def test_dash_prefix_quoted(self) -> None:
        assert _encode_value("-flag") == '"-flag"'

    def test_newline_quoted(self) -> None:
        assert _encode_value("hello\nworld") == '"hello\\nworld"'

    def test_carriage_return_quoted(self) -> None:
        assert _encode_value("hello\rworld") == '"hello\\rworld"'

    def test_tab_quoted(self) -> None:
        assert _encode_value("hello\tworld") == '"hello\\tworld"'


class TestEncode:
    """Tests for encode."""

    def test_produces_valid_toon(self, sample_repo_map: RepoMap) -> None:
        result = encode(sample_repo_map)
        assert result.startswith("repo: myproject")
        assert "root: myproject" in result
        assert "files[" in result
        assert "symbols[" in result
        assert "dependencies[" in result

    def test_files_tabular_format(self, sample_repo_map: RepoMap) -> None:
        result = encode(sample_repo_map)
        assert "files[3]{path,language,rank}:" in result

    def test_symbols_only_definitions(self, sample_repo_map: RepoMap) -> None:
        result = encode(sample_repo_map)
        lines = result.split("\n")
        # Find the symbols section
        sym_start = None
        for i, line in enumerate(lines):
            if line.startswith("symbols["):
                sym_start = i
                break
        assert sym_start is not None
        # Count symbols - should match definition count
        header = lines[sym_start]
        count = int(header.split("[")[1].split("]")[0])
        # We have 4 definitions in sample_file_infos: run, User, __init__, format_name
        assert count == 4

    def test_dependencies_in_output(self, sample_repo_map: RepoMap) -> None:
        result = encode(sample_repo_map)
        assert "dependencies[2]{source,target,symbols}:" in result
        assert "main.py" in result

    def test_signatures_with_special_chars_quoted(self) -> None:
        repo_map = RepoMap(
            repo_name="test",
            root=Path("/tmp/test"),
            files=[
                FileInfo(
                    path=Path("mod.py"),
                    language="python",
                    tags=[
                        Tag(
                            name="foo",
                            kind=TagKind.DEFINITION,
                            symbol_kind=SymbolKind.FUNCTION,
                            line=1,
                            file=Path("mod.py"),
                            signature="foo(x: int, y: str) -> dict[str, int]",
                        ),
                    ],
                ),
            ],
        )
        result = encode(repo_map)
        # The signature contains commas and colons, so it should be quoted
        assert '"foo(x: int, y: str) -> dict[str, int]"' in result

    def test_no_trailing_newline(self, sample_repo_map: RepoMap) -> None:
        result = encode(sample_repo_map)
        assert not result.endswith("\n")
