from argparse import ArgumentParser
from datetime import timedelta
from pathlib import Path
from typing import Iterator

from ltid.toolkit.log_graph import LogGraph
from ltid.toolkit.log_patterns import make_pattern_tree
from prefixspan import trie


def main(*args: str):
    argument_parser = ArgumentParser()
    argument_parser.add_argument("source_tree", type=Path)
    argument_parser.add_argument("log_files", type=Path, nargs="+")
    argument_parser.add_argument("--min_sequence_length", type=int, default=2)
    argument_parser.add_argument("--max_sequence_length", type=int, default=16)
    argument_parser.add_argument("--sequence_duration_ms", type=int, default=5)
    argument_parser.add_argument("--min_support_ratio", type=float, default=0.05)
    config = argument_parser.parse_args(args)

    log_graph = LogGraph.from_source(config.source_tree)
    pattern_tree = make_pattern_tree(
        config.log_files,
        timedelta(milliseconds=config.sequence_duration_ms),
        config.min_support_ratio,
    )

    for matched_patterns in match(log_graph, pattern_tree):
        print(matched_patterns)


def iter_edges(roots: trie) -> Iterator[tuple[int, int]]:
    edges: list[tuple[int, trie]] = [*roots]
    visited: set[int] = set()
    while len(edges) > 0:
        i, s = edges.pop()
        visited.add(i)
        for j, t in s:
            if j in visited:
                continue
            yield (i, j)
            edges.append((j, t))


def match(
    log_graph: LogGraph, pattern_tree: trie, max_intermediate_nodes: int = 0
) -> Iterator[list[int]]:
    visited: set[int] = set()

    def recurse(path: list[int], i: int, t: trie) -> Iterator[list[int]]:
        yield (path := path + [i])
        visited.add(i)
        for j, s in t:
            if (
                j in visited
                or len(log_graph.find_shortest_path(i, j)) > max_intermediate_nodes
            ):
                continue
            yield from recurse(path, j, s)

    for i, t in pattern_tree:
        yield from recurse([], i, t)


if __name__ == "__main__":
    main()
