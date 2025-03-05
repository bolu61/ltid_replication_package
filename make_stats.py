# !/usr/bin/env python3
import json
import pickle
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from ltid.toolkit.log_graph import LogGraph
from ltid.toolkit.query import is_id


def main():
    argparser = ArgumentParser()
    argparser.add_argument("--path", type=Path, default=Path.cwd())
    args = argparser.parse_args()

    with ThreadPoolExecutor() as executor:
        for path in cast(Path, args.path).iterdir():
            executor.submit(write_stats, path)


@dataclass
class LTIDStats:
    stmt_count: int
    stmt_w_id_count: int
    stmt_w_injection_count: int


def write_stats(path: Path):
    stats = get_stats(path)
    with open(path / "target" / "ltid_stats.json") as fp:
        json.dump(asdict(stats), fp)
        print(fp.name)


def get_stats(path: Path) -> LTIDStats:
    count = 0
    count_w_id = 0
    count_w_injection = 0

    with open(path / "target" / "log_graph.pkl", "rb") as fp:
        log_graph: LogGraph = pickle.load(fp)

    for logtype in log_graph:
        count += 1
        if any(is_id(variable) for variable in logtype.variables):
            count_w_id += 1
        for dominator in logtype.dominators:
            if any(is_id(variable) for variable in dominator.variables):
                count_w_injection += 1
    return LTIDStats(count, count_w_id, count_w_injection)


if __name__ == "__main__":
    main()
