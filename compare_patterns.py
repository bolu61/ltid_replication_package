#! /usr/bin/env python
import json
import logging
import pickle
import re
import sys
import traceback
from argparse import ArgumentParser, Namespace
from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from itertools import islice
from pathlib import Path
from typing import cast

import pandas as pd
from ltid.toolkit.log_graph import Loc, LogGraph
from ltid.toolkit.log_statement import LogStatement
from prefixspan import prefixspan

logging.basicConfig()
logger = logging.getLogger(__name__)

LOG_FORMAT_HADOOP = re.compile(
    r"^(?P<timestamp>[\d -:,]+) .*? \((?P<file_name>\w+.java):.+?\((?P<line_number>\d+)\)\) .*?$",
    flags=re.MULTILINE,
)


def main(argv: list[str]):
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--path", type=Path, default=Path.cwd())
    argument_parser.add_argument("--max_dataset_size", type=int, default=-1)
    argument_parser.add_argument("--min_sequence_length", type=int, default=2)
    argument_parser.add_argument("--max_sequence_length", type=int, default=16)
    argument_parser.add_argument("--window_size_ms", type=int, default=16)
    argument_parser.add_argument("--min_support", type=int, default=16)
    argument_parser.add_argument("--max_distance", type=float, default=0)
    argument_parser.add_argument("-v", "--verbose", action="store_true", default=False)
    argument_parser.add_argument("--vverbose", action="store_true", default=False)
    config = argument_parser.parse_args(argv[1:])

    if config.verbose:
        logger.setLevel(logging.INFO)
    if config.vverbose:
        logger.setLevel(logging.DEBUG)

    with ThreadPoolExecutor() as executor:
        for path in cast(Path, config.path).iterdir():
            executor.submit(write_config, path, config)


def with_exception[**T, S](f: Callable[T, S]):
    def g(*args: T.args, **kwargs: T.kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            traceback.print_exception(e)

    return g


@with_exception
def write_config(project_path: Path, config: Namespace):
    with open(project_path / "target" / "log_graph.pkl", "rb") as fp:
        log_graph: LogGraph = pickle.load(fp)
    loc_to_id_map = {log.loc: log.event_id for log in log_graph}

    logger.info(f"loaded log_graph {log_graph._graph}")

    sequences = [*dataset(config, project_path, loc_to_id_map)]

    trie = prefixspan(sequences, config.min_support)
    logger.info("built patterns")

    matching_paths = 0
    for path in log_graph.paths:
        if len(path) < 2:
            continue
        m = match(trie, path, config.max_distance)
        if m is None:
            continue
        matching_paths += 1

    data = {"matching_paths_count": matching_paths}
    with open(project_path / "target" / "ltid_comparison.json", "w") as fp:
        json.dump(data, fp)
        print(fp.name)


def dataset(config, path, loc_to_id_map) -> Iterator[Sequence[int]]:
    logger.info(f"loading logs from {path}")
    for file in path.glob("**/*-output.txt"):
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
    logger.info(f"loaded logs from {path}")


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


def match(t: prefixspan, seq: list[LogStatement], d: int) -> int | None:
    k = 0
    for s in seq:
        for n, t, j in beam(t, d - k):
            if n == s.event_id:
                break
        else:
            return None
        k = min(k, j)
    return k


def beam(trie, d: int) -> Iterator[tuple[int, prefixspan, int]]:
    queue = deque((n, t, 0) for n, t in trie)
    while queue:
        n, t, k = queue.popleft()
        yield n, t, k
        if k >= d:
            continue
        for m, s in t:
            queue.append((m, s, k + 1))


if __name__ == "__main__":
    main(sys.argv)
