"""Tests for dependency graph construction and PageRank ranking."""

from __future__ import annotations

from pathlib import Path

from repoguide.graph import build_graph, rank_files
from repoguide.models import FileInfo, SymbolKind, Tag, TagKind


class TestBuildGraph:
    """Tests for build_graph."""

    def test_creates_edges_for_cross_file_refs(
        self, sample_file_infos: list[FileInfo]
    ) -> None:
        graph, deps = build_graph(sample_file_infos)
        assert graph.number_of_edges() > 0
        assert any(
            d.source == Path("main.py") and d.target == Path("models.py") for d in deps
        )

    def test_no_self_edges(self) -> None:
        fi = FileInfo(
            path=Path("mod.py"),
            language="python",
            tags=[
                Tag(
                    name="foo",
                    kind=TagKind.DEFINITION,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=1,
                    file=Path("mod.py"),
                    signature="foo()",
                ),
                Tag(
                    name="foo",
                    kind=TagKind.REFERENCE,
                    symbol_kind=SymbolKind.FUNCTION,
                    line=5,
                    file=Path("mod.py"),
                ),
            ],
        )
        graph, deps = build_graph([fi])
        assert graph.number_of_edges() == 0
        assert len(deps) == 0

    def test_all_files_are_nodes(self, sample_file_infos: list[FileInfo]) -> None:
        graph, _ = build_graph(sample_file_infos)
        for fi in sample_file_infos:
            assert fi.path in graph.nodes

    def test_dependencies_aggregated(self, sample_file_infos: list[FileInfo]) -> None:
        _, deps = build_graph(sample_file_infos)
        main_to_models = [
            d
            for d in deps
            if d.source == Path("main.py") and d.target == Path("models.py")
        ]
        assert len(main_to_models) == 1
        assert "User" in main_to_models[0].symbols

    def test_multiple_targets(self, sample_file_infos: list[FileInfo]) -> None:
        _, deps = build_graph(sample_file_infos)
        main_deps = [d for d in deps if d.source == Path("main.py")]
        targets = {d.target for d in main_deps}
        assert Path("models.py") in targets
        assert Path("utils.py") in targets


class TestRankFiles:
    """Tests for rank_files."""

    def test_assigns_ranks(self, sample_file_infos: list[FileInfo]) -> None:
        graph, _ = build_graph(sample_file_infos)
        rank_files(graph, sample_file_infos)
        for fi in sample_file_infos:
            assert fi.rank >= 0.0

    def test_ranks_approximately_sum_to_one(
        self, sample_file_infos: list[FileInfo]
    ) -> None:
        graph, _ = build_graph(sample_file_infos)
        rank_files(graph, sample_file_infos)
        total = sum(fi.rank for fi in sample_file_infos)
        assert abs(total - 1.0) < 0.01

    def test_more_referenced_file_ranked_higher(
        self, sample_file_infos: list[FileInfo]
    ) -> None:
        graph, _ = build_graph(sample_file_infos)
        rank_files(graph, sample_file_infos)
        # models.py and utils.py are referenced by main.py, so they should
        # rank higher than main.py (which is only a referencing file)
        rank_by_path = {fi.path: fi.rank for fi in sample_file_infos}
        assert rank_by_path[Path("models.py")] > rank_by_path[Path("main.py")]

    def test_empty_graph_uniform_rank(self) -> None:
        fi1 = FileInfo(path=Path("a.py"), language="python")
        fi2 = FileInfo(path=Path("b.py"), language="python")
        infos = [fi1, fi2]
        graph, _ = build_graph(infos)
        rank_files(graph, infos)
        assert abs(infos[0].rank - infos[1].rank) < 0.001

    def test_sorted_by_rank_descending(self, sample_file_infos: list[FileInfo]) -> None:
        graph, _ = build_graph(sample_file_infos)
        rank_files(graph, sample_file_infos)
        ranks = [fi.rank for fi in sample_file_infos]
        assert ranks == sorted(ranks, reverse=True)

    def test_returns_none(self, sample_file_infos: list[FileInfo]) -> None:
        graph, _ = build_graph(sample_file_infos)
        result = rank_files(graph, sample_file_infos)
        assert result is None
