import pickle
import traceback
from argparse import ArgumentParser
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from ltid.toolkit.log_graph import LogGraph


def main():
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--path", type=Path, default=Path.cwd())
    args = argument_parser.parse_args()

    with ThreadPoolExecutor() as executor:
        for path in cast(Path, args.path).iterdir():
            executor.submit(write_log_graph, path)


def with_exception[**T, S](f: Callable[T, S]):
    def g(*args: T.args, **kwargs: T.kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            traceback.print_exception(e)

    return g


@with_exception
def write_log_graph(path: Path):
    log_graph = LogGraph.from_source(path)
    (path / "target").mkdir(exist_ok=True)
    with open(path / "target" / "log_graph.pkl", "wb") as fp:
        pickle.dump(log_graph, fp)
        print(fp.name)


if __name__ == "__main__":
    main()
