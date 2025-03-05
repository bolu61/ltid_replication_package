import csv
from collections.abc import Callable, Generator, Iterable, Iterator
from datetime import datetime
from importlib import resources
from pathlib import Path
from subprocess import PIPE, Popen

import networkx as nx
from ltid.toolkit.log_statement import LogStatement

__all__ = ["LogGraph"]

type Loc = tuple[str, int]
type _LogParser = Callable[[Iterable[str]], Iterator[tuple[datetime, int]]]


class LogGraph:
    _graph: nx.DiGraph
    _loc: dict[Loc, int]

    def __init__(self):
        self._graph = nx.DiGraph()
        self._loc = dict()

    @staticmethod
    def from_source(target_path: Path, launcher: str = "file") -> "LogGraph":
        log_graph = LogGraph()
        for (
            idom_id,
            event_id,
            path,
            _,
            _,
            _,
            line_number,
            level,
            template,
        ) in extract_log_statements(target_path, launcher=launcher):
            event_id = int(event_id)
            idom_id = int(idom_id)
            if idom_id < 0:
                idom_id = None
            log_graph._graph.add_node(
                event_id,
                file_name=Path(path).name,
                line_number=int(line_number),
                level=level.upper(),
                template=template,
            )
            if idom_id is not None:
                log_graph._graph.add_edge(event_id, idom_id)
        return log_graph

    def get_statement(self, event_id: int):
        return LogStatement(self._graph, event_id)

    def __iter__(self) -> Generator[LogStatement]:
        yield from map(self.get_statement, self._graph.nodes)

    @property
    def roots(self) -> Generator[LogStatement]:
        for n, d in self._graph.out_degree():
            if d > 0:
                continue
            yield self.get_statement(n)

    @property
    def leafs(self) -> Iterator[LogStatement]:
        for n, d in self._graph.in_degree():
            if d > 0:
                continue
            yield self.get_statement(n)

    @property
    def paths(self) -> Generator[list[LogStatement]]:
        def rec(node: int, path: list[LogStatement]) -> Generator[list[LogStatement]]:
            path = path + [self.get_statement(node)]
            if self._graph.in_degree(node) == 0:
                yield path
                return
            for child in self._graph.predecessors(node):
                yield from rec(child, path)

        for root in self.roots:
            yield from rec(root.event_id, [])


LTID_LOG_GRAPH_CLASSPATH = (
    resources.files((__package__ or "__main__").split(".")[0]) / "include" / "*"
)


def extract_log_statements(path: Path, launcher: str = "file") -> Iterator[list[str]]:
    if not path.exists():
        raise ValueError(f"{path=} does not exist")
    proc = Popen(
        [
            "java",
            "-cp",
            str(LTID_LOG_GRAPH_CLASSPATH),
            "ltid.log_graph.Launcher",
            "--environment",
            f"{launcher}:{path}",
            "output",
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    assert proc.stdout is not None
    assert proc.stderr is not None

    yield from csv.reader(proc.stdout, quoting=csv.QUOTE_ALL)

    if proc.wait() != 0:
        raise LTIDLogGraphExecutionError(
            {
                "command": proc.args,
                "returncode": proc.returncode,
                "message": proc.stderr.readlines(),
                "classpath": LTID_LOG_GRAPH_CLASSPATH,
            }
        )


class LTIDLogGraphExecutionError(Exception):
    pass
