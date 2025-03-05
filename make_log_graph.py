#! /usr/bin/env python
import pickle
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ltid.toolkit.log_graph import LogGraph


def main():
    argument_parser = ArgumentParser()
    argument_parser.add_argument("path", type=Path, nargs="*", default=Path.cwd())
    args = argument_parser.parse_args()
    
    with ThreadPoolExecutor() as executor:
        executor.map(write_log_graph, args.path)


def write_log_graph(path: Path):
    log_graph = LogGraph.from_source(path)
    with open(path / "target"/ "source_log_graph.pkl", "wb") as fp:
        pickle.dump(log_graph, fp)
        print(fp.name)


if __name__ == "__main__":
    main()
