"""Dependency graph construction and PageRank ranking."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import networkx as nx

from repoguide.models import Dependency, FileInfo, TagKind


def build_graph(
    file_infos: list[FileInfo],
) -> tuple[nx.MultiDiGraph, list[Dependency]]:
    """Build a dependency graph from extracted tags.

    Nodes are file paths. An edge from file A to file B exists when file A
    contains a reference to a symbol defined in file B.

    Args:
        file_infos: List of FileInfo with extracted tags.

    Returns:
        Tuple of (graph, dependencies list).
    """
    defines: dict[str, set[Path]] = defaultdict(set)
    for fi in file_infos:
        for tag in fi.tags:
            if tag.kind == TagKind.DEFINITION:
                defines[tag.name].add(fi.path)

    graph = nx.MultiDiGraph()
    for fi in file_infos:
        graph.add_node(fi.path)

    edge_symbols: dict[tuple[Path, Path], list[str]] = defaultdict(list)

    for fi in file_infos:
        for tag in fi.tags:
            if tag.kind != TagKind.REFERENCE:
                continue
            for def_file in sorted(defines.get(tag.name, set())):
                if def_file == fi.path:
                    continue
                graph.add_edge(fi.path, def_file, symbol=tag.name)
                if tag.name not in edge_symbols[(fi.path, def_file)]:
                    edge_symbols[(fi.path, def_file)].append(tag.name)

    dependencies = [
        Dependency(source=src, target=tgt, symbols=syms)
        for (src, tgt), syms in edge_symbols.items()
    ]

    return graph, dependencies


def rank_files(
    graph: nx.MultiDiGraph,
    file_infos: list[FileInfo],
) -> None:
    """Apply PageRank to the graph and update file_infos in place.

    Mutates file_infos: sets each item's rank field and sorts the list
    by rank descending.

    Args:
        graph: The dependency MultiDiGraph.
        file_infos: List of FileInfo to update in place.
    """
    if graph.number_of_edges() == 0:
        uniform = 1.0 / max(len(file_infos), 1)
        for fi in file_infos:
            fi.rank = uniform
    else:
        ranks = nx.pagerank(graph, alpha=0.85)
        for fi in file_infos:
            fi.rank = ranks.get(fi.path, 0.0)

    file_infos.sort(key=lambda fi: fi.rank, reverse=True)
