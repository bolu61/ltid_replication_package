#! /usr/bin/env python
import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterable
from datetime import datetime, timedelta
from functools import partial
from math import floor
from pathlib import Path
from typing import Iterator, Mapping

import pandas as pd
from ltid.toolkit.log_graph import Loc, LogGraph
from nltk import edit_distance
from prefixspan import make_trie

LOG_FORMAT_HADOOP = re.compile(
    r"^(?P<timestamp>[\d -:,]+) .*? \((?P<file_name>\w+).java:.+?\((?P<line_number>\d+)\)\) .*?$",
    flags=re.MULTILINE,
)


def main(argv: list[str]):
    argument_parser = ArgumentParser()
    argument_parser.add_argument("source_tree", type=Path)
    argument_parser.add_argument("log_files", type=Path, nargs="+")
    argument_parser.add_argument("--min_sequence_length", type=int, default=2)
    argument_parser.add_argument("--max_sequence_length", type=int, default=16)
    argument_parser.add_argument("--window_size_ms", type=int, default=5)
    argument_parser.add_argument("--min_support_ratio", type=float, default=0.05)
    config = argument_parser.parse_args(argv[1:])

    source_log_graph = LogGraph.from_source(config.source_tree)
    loc_to_id_map = {log.loc: log.event_id for log in source_log_graph}

    @partial(lambda x: [*x()])
    def dataset():
        for file in config.log_files:
            with file.open("r") as logs:
                timestamp, event_ids = zip(*parse_log(loc_to_id_map, logs))
                series = pd.Series(event_ids, index=timestamp)
                yield from series.rolling(
                    timedelta(milliseconds=config.window_size_ms),
                    min_periods=config.min_sequence_length,
                )

    pattern_tree = make_trie(dataset, floor(config.min_support_ratio * len(dataset)))

    patterns_log_graph = LogGraph.from_patterns(pattern_tree)

    a = {*source_log_graph.paths}
    b = {*patterns_log_graph.paths}
    
    matching_paths = len(a & b)
    all_paths = len(a | b)

    return f"{matching_paths=} {all_paths=}"


def parse_log(
    loc_to_id_map: Mapping[Loc, int], logs: Iterable[str]
) -> Iterator[tuple[datetime, int]]:
    for log in logs:
        if match := re.match(LOG_FORMAT_HADOOP, log):
            dt = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S,%f")
            loc = (match.group("file_name"), int(match.group("line_number")))
            yield dt, loc_to_id_map[loc]


def log_graph_path_distance(a: list[int], b: list[int]) -> int:
    """calculate cyclic edit distance between two paths, without substitution"""
    if len(a) > len(b):
        a, b = b, a
    return edit_distance(a + a, b, substitution_cost=2) - len(a)


if __name__ == "__main__":
    main(sys.argv)
