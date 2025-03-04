#! /usr/bin/env python
import logging
import pickle
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
    argument_parser.add_argument("data_path", type=Path)
    argument_parser.add_argument("--min_similarity", type=float, default=0.8)
    argument_parser.add_argument("-v", "--verbose", action="store_true", default=False)
    argument_parser.add_argument("--vverbose", action="store_true", default=False)
    config = argument_parser.parse_args(argv[1:])

    if config.verbose:
        logger.setLevel(logging.INFO)
    if config.vverbose:
        logger.setLevel(logging.DEBUG)

    with open(config.data_path / "source_log_graph.pkl", "rb") as fp:
        source_log_graph = pickle.load(fp)

    with open(config.data_path / "patterns_log_graph.pkl", "rb") as fp:
        patterns_log_graph = pickle.load(fp)

    source_paths = {p for p in source_log_graph.paths if len(p) >= 2}
    patterns_paths = {p for p in patterns_log_graph.paths if len(p) >= 2}

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
