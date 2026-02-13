"""Language registry for tree-sitter grammars and queries."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from importlib import resources
from typing import TYPE_CHECKING

from tree_sitter_language_pack import get_language, get_parser

if TYPE_CHECKING:
    from tree_sitter import Language, Parser, Query


EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
}


@functools.cache
def _cached_parser(name: str) -> Parser:
    """Return a cached tree-sitter Parser for the given language."""
    return get_parser(name)


@functools.cache
def _cached_tag_query(name: str) -> Query:
    """Return a cached compiled tag query for the given language."""
    from tree_sitter import Query as TSQuery

    scm_text = _load_query_file(name)
    lang = get_language(name)
    return TSQuery(lang, scm_text)


@dataclass(frozen=True)
class TreeSitterLanguage:
    """A tree-sitter language with its tag query."""

    name: str
    extensions: tuple[str, ...]

    def get_language(self) -> Language:
        """Get the tree-sitter Language object."""
        return get_language(self.name)

    def get_parser(self) -> Parser:
        """Get a configured tree-sitter Parser (cached)."""
        return _cached_parser(self.name)

    def get_tag_query(self) -> Query:
        """Load and compile the tag query for this language (cached)."""
        return _cached_tag_query(self.name)


LANGUAGES: dict[str, TreeSitterLanguage] = {
    "python": TreeSitterLanguage(name="python", extensions=(".py",)),
}


def _load_query_file(language_name: str) -> str:
    """Load a .scm query file from the queries package.

    Args:
        language_name: The language name matching the .scm filename.

    Returns:
        The query file contents as a string.

    Raises:
        FileNotFoundError: If no query file exists for the language.
    """
    query_path = resources.files("sourcecrumb.queries").joinpath(f"{language_name}.scm")
    return query_path.read_text(encoding="utf-8")


def language_for_extension(ext: str) -> TreeSitterLanguage | None:
    """Look up a language config by file extension.

    Args:
        ext: File extension including the dot (e.g., ".py").

    Returns:
        The TreeSitterLanguage config, or None if unsupported.
    """
    lang_name = EXTENSION_MAP.get(ext)
    if lang_name is None:
        return None
    return LANGUAGES.get(lang_name)
