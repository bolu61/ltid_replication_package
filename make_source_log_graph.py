#! /usr/bin/env python
import pickle
import sys
from argparse import ArgumentParser
from pathlib import Path

from ltid.toolkit.log_graph import LogGraph


def main(argv: list[str]):
    argument_parser = ArgumentParser()
    argument_parser.add_argument("source_tree", type=Path)
    config = argument_parser.parse_args(argv[1:])

    log_graph = LogGraph.from_source(config.source_tree)
    with open(config.source_tree / "source_log_graph.pkl", "wb") as fp:
        pickle.dump(log_graph, fp)
        print(f"written output to file {fp.name}")


if __name__ == "__main__":
    main(sys.argv)
