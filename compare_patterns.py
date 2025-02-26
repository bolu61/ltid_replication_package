#! /usr/bin/env python
from itertools import islice
import logging
import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timedelta
from functools import partial
from math import floor
from pathlib import Path

import pandas as pd
from ltid.toolkit.log_graph import Loc, LogGraph
from nltk import edit_distance
from prefixspan import prefixspan

logger = logging.getLogger(__name__)

LOG_FORMAT_HADOOP = re.compile(
    r"^(?P<timestamp>[\d -:,]+) .*? \((?P<file_name>\w+.java):.+?\((?P<line_number>\d+)\)\) .*?$",
    flags=re.MULTILINE,
)


def main(argv: list[str]):
    argument_parser = ArgumentParser()
    argument_parser.add_argument("source_tree", type=Path)
    argument_parser.add_argument("log_files", type=Path, nargs="+")
    argument_parser.add_argument("--max_dataset_size", type=int, default=-1)
    argument_parser.add_argument("--min_sequence_length", type=int, default=2)
    argument_parser.add_argument("--max_sequence_length", type=int, default=16)
    argument_parser.add_argument("--window_size_ms", type=int, default=5)
    argument_parser.add_argument("--min_support_ratio", type=float, default=0.05)
    config = argument_parser.parse_args(argv[1:])

    logger.info("building source log graph")

    source_log_graph = LogGraph.from_source(config.source_tree)
    loc_to_id_map = {log.loc: log.event_id for log in source_log_graph}

    logger.info("parsing logs")

    @partial(lambda x: [*x()])
    def dataset():
        for file in config.log_files:
            try:
                timestamp, event_ids = zip(*parse_log(loc_to_id_map, file))
            except ValueError as e:
                logger.debug(f"in {file=}, no logs were parsed", exc_info=e)
                return
            series = pd.Series(event_ids, index=timestamp).sort_index()
            sequences = series.rolling(
                timedelta(milliseconds=config.window_size_ms),
            )
            if config.max_dataset_size > 0:
                sequences = islice(sequences, config.max_dataset_size)
            for sequence in sequences:
                if len(sequence) < config.min_sequence_length:
                    continue
                yield sequence[:config.max_sequence_length].to_list()

    logger.info(f"building prefixspan with {len(dataset)} sequences")

    pattern_tree = prefixspan(dataset, floor(config.min_support_ratio * len(dataset)))

    patterns_log_graph = LogGraph.from_patterns(pattern_tree)

    logger.info("calculating path distance")

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
                logger.debug(f"in {log_file=} failed to parse {log=}", exc_info=e)
                continue


def log_graph_path_distance(a: Sequence[int], b: Sequence[int]) -> int:
    """calculate cyclic edit distance between two paths, without substitution"""
    if len(a) < len(b):
        a, b = b, a
    return edit_distance([*a, *a], b, substitution_cost=2) - len(a)


if __name__ == "__main__":
    main(sys.argv)
