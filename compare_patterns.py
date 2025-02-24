#! /usr/bin/env python
import logging
import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterable
from datetime import datetime, timedelta
from functools import partial
from math import floor
from pathlib import Path
from typing import Iterator, Mapping

import numpy as np
import pandas as pd
from ltid.toolkit.log_graph import Loc, LogGraph
from nltk import edit_distance
from prefixspan import make_trie

logger = logging.getLogger(__name__)

LOG_FORMAT_HADOOP = re.compile(
    r"^(?P<timestamp>[\d -:,]+) .*? \((?P<file_name>\w+.java):.+?\((?P<line_number>\d+)\)\) .*?$",
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

    @partial(lambda x: [*map(np.array, x())])
    def dataset():
        for file in config.log_files:
            try:
                timestamp, event_ids = zip(*parse_log(loc_to_id_map, file))
            except ValueError as e:
                logger.debug(f"in {file=}, no logs were parsed", exc_info=e)
                return
            series = pd.Series(event_ids, index=timestamp).sort_index()
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

    print(f"{matching_paths=}", f"{all_paths=}")


def parse_log(
    loc_to_id_map: Mapping[Loc, int], log_file: Path
) -> Iterator[tuple[datetime, int]]:
    with log_file.open() as f:
        for log in f:
            try:
                if not (match := re.match(LOG_FORMAT_HADOOP, log)):
                    continue
                if (
                    loc := (match.group("file_name"), int(match.group("line_number")))
                ) not in loc_to_id_map:
                    logger.debug(f"unmatched log with {loc=}")
                    continue
                dt = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S,%f")
                yield dt, loc_to_id_map[loc]
            except Exception as e:
                logger.exception(f"in {log_file=} failed to parse {log=}", exc_info=e)
                continue


def log_graph_path_distance(a: list[int], b: list[int]) -> int:
    """calculate cyclic edit distance between two paths, without substitution"""
    if len(a) > len(b):
        a, b = b, a
    return edit_distance(a + a, b, substitution_cost=2) - len(a)


if __name__ == "__main__":
    main(sys.argv)
