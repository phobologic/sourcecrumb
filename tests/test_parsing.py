"""Tests for tree-sitter tag extraction."""

from __future__ import annotations

from pathlib import Path

from sourcecrumb.languages import LANGUAGES
from sourcecrumb.models import SymbolKind, TagKind
from sourcecrumb.parsing import extract_tags

PYTHON = LANGUAGES["python"]


class TestExtractTags:
    """Integration tests for extract_tags using real tree-sitter parsing."""

    def test_extracts_class_definition(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("class Foo:\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert len(defs) == 1
        assert defs[0].name == "Foo"
        assert defs[0].symbol_kind == SymbolKind.CLASS

    def test_extracts_function_definition(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("def bar():\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert len(defs) == 1
        assert defs[0].name == "bar"
        assert defs[0].symbol_kind == SymbolKind.FUNCTION

    def test_extracts_method(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text(
            "class Foo:\n    def method(self):\n        pass\n",
            encoding="utf-8",
        )
        tags = extract_tags(f, PYTHON)
        methods = [
            t
            for t in tags
            if t.kind == TagKind.DEFINITION and t.symbol_kind == SymbolKind.METHOD
        ]
        assert len(methods) == 1
        assert methods[0].name == "Foo.method"

    def test_extracts_call_reference(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("foo()\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        refs = [t for t in tags if t.kind == TagKind.REFERENCE]
        assert len(refs) == 1
        assert refs[0].name == "foo"

    def test_extracts_attribute_call(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("obj.method()\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        refs = [t for t in tags if t.kind == TagKind.REFERENCE]
        assert len(refs) == 1
        assert refs[0].name == "method"

    def test_extracts_import_reference(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("from os import path\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        refs = [t for t in tags if t.kind == TagKind.REFERENCE]
        assert any(r.name == "path" for r in refs)

    def test_line_numbers_are_one_indexed(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("# comment\ndef foo():\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        foo = [t for t in tags if t.name == "foo" and t.kind == TagKind.DEFINITION]
        assert foo[0].line == 2

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        assert tags == []

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        import pytest

        with pytest.raises(FileNotFoundError):
            extract_tags(tmp_path / "nope.py", PYTHON)


class TestSignatureExtraction:
    """Tests for definition signature capture."""

    def test_function_signature_with_params(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text(
            "def process(items: list[str], verbose: bool = False) -> int:\n    pass\n",
            encoding="utf-8",
        )
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert (
            defs[0].signature
            == "process(items: list[str], verbose: bool = False) -> int"
        )

    def test_function_signature_no_return(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("def simple(x):\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert defs[0].signature == "simple(x)"

    def test_class_signature_with_bases(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("class App(Base, Mixin):\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert defs[0].signature == "App(Base, Mixin)"

    def test_class_signature_no_bases(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("class Plain:\n    pass\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        defs = [t for t in tags if t.kind == TagKind.DEFINITION]
        assert defs[0].signature == "Plain"

    def test_method_signature(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text(
            "class Foo:\n    def run(self, cfg: Config) -> None:\n        pass\n",
            encoding="utf-8",
        )
        tags = extract_tags(f, PYTHON)
        methods = [
            t
            for t in tags
            if t.kind == TagKind.DEFINITION and t.symbol_kind == SymbolKind.METHOD
        ]
        assert methods[0].name == "Foo.run"
        assert methods[0].signature == "run(self, cfg: Config) -> None"

    def test_references_have_no_signature(self, tmp_path: Path) -> None:
        f = tmp_path / "mod.py"
        f.write_text("foo()\n", encoding="utf-8")
        tags = extract_tags(f, PYTHON)
        refs = [t for t in tags if t.kind == TagKind.REFERENCE]
        assert refs[0].signature == ""
