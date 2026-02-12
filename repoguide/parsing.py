"""Tree-sitter parsing and tag extraction with signature capture."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, QueryCursor

from repoguide.languages import TreeSitterLanguage
from repoguide.models import SymbolKind, Tag, TagKind

_CAPTURE_MAP: dict[str, tuple[TagKind, SymbolKind]] = {
    "definition.class": (TagKind.DEFINITION, SymbolKind.CLASS),
    "definition.function": (TagKind.DEFINITION, SymbolKind.FUNCTION),
    "reference.call": (TagKind.REFERENCE, SymbolKind.FUNCTION),
    "reference.import": (TagKind.REFERENCE, SymbolKind.MODULE),
}


def extract_tags(file_path: Path, language: TreeSitterLanguage) -> list[Tag]:
    """Parse a file and extract all definition and reference tags.

    Args:
        file_path: Absolute path to the source file.
        language: The tree-sitter language configuration.

    Returns:
        List of Tag objects found in the file.

    Raises:
        FileNotFoundError: If file_path does not exist.
    """
    source = file_path.read_bytes()
    if not source:
        return []

    parser = language.get_parser()
    tree = parser.parse(source)
    query = language.get_tag_query()
    cursor = QueryCursor(query)
    matches = cursor.matches(tree.root_node)

    tags: list[Tag] = []
    for _pattern_idx, match_dict in matches:
        name_nodes = match_dict.get("name", [])
        if not name_nodes:
            continue
        name_node = name_nodes[0]
        name_text = name_node.text.decode("utf-8")

        for capture_name, nodes in match_dict.items():
            if capture_name == "name":
                continue
            if capture_name not in _CAPTURE_MAP:
                continue

            tag_kind, symbol_kind = _CAPTURE_MAP[capture_name]
            def_node = nodes[0]
            effective_name = name_text

            if (
                tag_kind == TagKind.DEFINITION
                and symbol_kind == SymbolKind.FUNCTION
                and _is_method(def_node)
            ):
                symbol_kind = SymbolKind.METHOD
                class_name = _get_enclosing_class_name(def_node)
                if class_name:
                    effective_name = f"{class_name}.{name_text}"

            signature = ""
            if tag_kind == TagKind.DEFINITION:
                signature = _extract_signature(def_node, symbol_kind)

            tags.append(
                Tag(
                    name=effective_name,
                    kind=tag_kind,
                    symbol_kind=symbol_kind,
                    line=name_node.start_point[0] + 1,
                    file=file_path,
                    signature=signature,
                )
            )

    return tags


def _get_enclosing_class_name(func_node: Node) -> str | None:
    """Return the name of the enclosing class, or None if not inside a class."""
    parent = func_node.parent
    if parent is None:
        return None
    class_node = None
    if (
        parent.type == "block"
        and parent.parent
        and parent.parent.type == "class_definition"
    ):
        class_node = parent.parent
    elif parent.type == "decorated_definition":
        grandparent = parent.parent
        if (
            grandparent
            and grandparent.type == "block"
            and grandparent.parent
            and grandparent.parent.type == "class_definition"
        ):
            class_node = grandparent.parent
    if class_node is None:
        return None
    for child in class_node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8")
    return None


def _is_method(func_node: Node) -> bool:
    """Check if a function_definition node is a method (inside a class)."""
    parent = func_node.parent
    if parent is None:
        return False
    if (
        parent.type == "block"
        and parent.parent
        and parent.parent.type == "class_definition"
    ):
        return True
    # Decorated methods: function_definition -> decorated_definition -> block -> class
    if parent.type == "decorated_definition":
        grandparent = parent.parent
        if (
            grandparent
            and grandparent.type == "block"
            and grandparent.parent
            and grandparent.parent.type == "class_definition"
        ):
            return True
    return False


def _extract_signature(def_node: Node, symbol_kind: SymbolKind) -> str:
    """Extract the signature string from a definition node.

    Args:
        def_node: The tree-sitter definition node (class_definition or
            function_definition).
        symbol_kind: The kind of symbol.

    Returns:
        The signature string (e.g., "main(config: Config) -> None").
    """
    if symbol_kind == SymbolKind.CLASS:
        return _extract_class_signature(def_node)
    return _extract_function_signature(def_node)


def _extract_class_signature(node: Node) -> str:
    """Extract class signature like 'MyClass(Base, Mixin)'."""
    name = ""
    args = ""
    for child in node.children:
        if child.type == "identifier":
            name = child.text.decode("utf-8")
        elif child.type == "argument_list":
            args = child.text.decode("utf-8")
    return f"{name}{args}" if args else name


def _extract_function_signature(node: Node) -> str:
    """Extract function signature like 'run(self, config: Config) -> None'."""
    name = ""
    params = ""
    return_type = ""
    for child in node.children:
        if child.type == "identifier":
            name = child.text.decode("utf-8")
        elif child.type == "parameters":
            params = _collapse_whitespace(child.text.decode("utf-8"))
        elif child.type == "type":
            return_type = child.text.decode("utf-8")
    sig = f"{name}{params}"
    if return_type:
        sig += f" -> {return_type}"
    return sig


def _collapse_whitespace(text: str) -> str:
    """Collapse multi-line whitespace into single spaces."""
    import re

    return re.sub(r"\s+", " ", text)
