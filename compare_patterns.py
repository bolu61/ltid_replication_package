#! /usr/bin/env python
import logging
import re
import sys
from argparse import ArgumentParser
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timedelta
from itertools import islice
from pathlib import Path

import pandas as pd
from ltid.toolkit.log_graph import Loc, LogGraph, LogStatement
from nltk import edit_distance
from prefixspan import prefixspan

logging.basicConfig()
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
    argument_parser.add_argument("--min_support", type=int, default=30)
    argument_parser.add_argument("--min_similarity", type=float, default=0.8)
    argument_parser.add_argument("-v", "--verbose", action="store_true", default=False)
    argument_parser.add_argument("--vverbose", action="store_true", default=False)
    config = argument_parser.parse_args(argv[1:])

    if config.verbose:
        logger.setLevel(logging.INFO)
    if config.vverbose:
        logger.setLevel(logging.DEBUG)

    logger.info("building source log graph")

    source_log_graph = LogGraph.from_source(config.source_tree)
    loc_to_id_map = {log.loc: log.event_id for log in source_log_graph}

    logger.info("parsing logs")

    @lambda f: [*f()]
    def dataset() -> Iterator[Sequence[int]]:
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
                yield sequence[: config.max_sequence_length].to_list()

    logger.info(f"building prefixspan with {len(dataset)} sequences")

    pattern_tree = prefixspan(dataset, config.min_support)

    patterns_log_graph = LogGraph.from_patterns(pattern_tree)

    logger.info("calculating path distance")

    source_paths = {*source_log_graph.paths}
    patterns_paths = {*patterns_log_graph.paths}

    matching_paths = 0
    source_paths_len = len(source_paths)
    patterns_paths_len = len(patterns_paths)

    for source_path in source_paths:
        for patterns_path in patterns_paths:
            if log_sequence_similarity(patterns_path, source_path) > config.min_similarity:
                matching_paths += 1
                break

    print(
        f"{source_paths_len}",
        f"{patterns_paths_len}",
        f"{matching_paths=}",
        sep=", ",
    )


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


def log_sequence_similarity(
    a: Sequence[LogStatement], b: Sequence[LogStatement]
) -> float:
    """calculate cyclic edit distance between two paths, without substitution"""
    a_id = [ls.event_id for ls in a]
    b_id = [ls.event_id for ls in b]

    # handle cyclic patterns by repeating the longest sequence
    if len(a) < len(b):
        a, b = b, a
    d = edit_distance(a_id * 2, b_id, substitution_cost=2) - len(a)
    return 1 - d / (len(a) + len(b))


if __name__ == "__main__":
    main(sys.argv)
