import re
from argparse import ArgumentParser
from collections.abc import Sequence
from datetime import timedelta
from itertools import chain
from math import floor
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd
from ltid.toolkit.log_graph import LogGraph
from ltid.toolkit.log_patterns import make_pattern_tree
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import ArrayLike
from prefixspan import make_trie, trie


def main():
    argument_parser = ArgumentParser()
    argument_parser.add_argument("source_tree", type=Path)
    argument_parser.add_argument("log_files", type=Path, nargs="+")
    argument_parser.add_argument("--min_sequence_length", type=int, default=2)
    argument_parser.add_argument("--max_sequence_length", type=int, default=16)
    argument_parser.add_argument("--sequence_duration_ms", type=int, default=5)
    argument_parser.add_argument("--min_support_ratio", type=float, default=0.05)
    args = argument_parser.parse_args()

    log_graph = LogGraph.from_source(args.source_tree)
    pattern_tree = make_pattern_tree(
        args.log_files,
        timedelta(milliseconds=args.sequence_duration_ms),
        args.min_support_ratio,
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
