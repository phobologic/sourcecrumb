"""Token-budget-aware file and symbol selection."""

from __future__ import annotations

from repoguide.models import RepoMap


def select_files(
    repo_map: RepoMap,
    *,
    max_files: int | None = None,
) -> RepoMap:
    """Select top-ranked files up to a limit.

    Args:
        repo_map: The full RepoMap (files should already be sorted by rank).
        max_files: Maximum number of files to include. None means all.

    Returns:
        A new RepoMap with only selected files and their dependencies.
    """
    if max_files is None or max_files >= len(repo_map.files):
        return repo_map

    selected_files = repo_map.files[:max_files]
    selected_paths = {fi.path for fi in selected_files}

    selected_deps = [
        d
        for d in repo_map.dependencies
        if d.source in selected_paths and d.target in selected_paths
    ]

    return RepoMap(
        repo_name=repo_map.repo_name,
        root=repo_map.root,
        files=selected_files,
        dependencies=selected_deps,
    )
