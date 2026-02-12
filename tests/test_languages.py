"""Tests for the language registry."""

from __future__ import annotations

from tree_sitter import Query

from repoguide.languages import LANGUAGES, language_for_extension


class TestLanguageForExtension:
    """Tests for extension-to-language lookup."""

    def test_python_extension(self) -> None:
        lang = language_for_extension(".py")
        assert lang is not None
        assert lang.name == "python"

    def test_unknown_extension_returns_none(self) -> None:
        assert language_for_extension(".xyz") is None

    def test_no_dot_returns_none(self) -> None:
        assert language_for_extension("py") is None


class TestTreeSitterLanguage:
    """Tests for TreeSitterLanguage configuration."""

    def test_get_parser(self) -> None:
        lang = LANGUAGES["python"]
        parser = lang.get_parser()
        assert parser is not None

    def test_get_tag_query_returns_query(self) -> None:
        lang = LANGUAGES["python"]
        query = lang.get_tag_query()
        assert isinstance(query, Query)

    def test_get_tag_query_has_patterns(self) -> None:
        lang = LANGUAGES["python"]
        query = lang.get_tag_query()
        assert query.pattern_count > 0

    def test_get_parser_returns_same_instance(self) -> None:
        lang = LANGUAGES["python"]
        assert lang.get_parser() is lang.get_parser()

    def test_get_tag_query_returns_same_instance(self) -> None:
        lang = LANGUAGES["python"]
        assert lang.get_tag_query() is lang.get_tag_query()
