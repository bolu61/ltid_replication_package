import csv
import re
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from pathlib import Path
from subprocess import PIPE, Popen
from typing import cast

import networkx as nx
from prefixspan import prefixspan

LTID_LOG_GRAPH_CLASSPATH = (
    resources.files((__package__ or "__main__").split(".")[0]) / "include" / "*"
)


type Loc = tuple[str, int]
type _LogParser = Callable[[Iterable[str]], Iterator[tuple[datetime, int]]]


class LogGraph:
    _graph: nx.DiGraph
    _loc: dict[Loc, int]

    def __init__(self):
        self._graph = nx.DiGraph()
        self._loc = dict()

    def __getitem__(self, event_id: int):
        return LogStatement(self._graph, event_id)

    def __iter__(self) -> Iterator["LogStatement"]:
        return map(self.__getitem__, filter(lambda x: x >= 0, self._graph.nodes))

    @property
    def roots(self) -> tuple["LogStatement", ...]:
        return tuple(self[n] for n, d in self._graph.in_degree() if d == 0)

    @property
    def leafs(self) -> tuple["LogStatement", ...]:
        return tuple(self[n] for n, d in self._graph.out_degree() if d == 0)

    @property
    def paths(self) -> Iterator[tuple["LogStatement", ...]]:
        for root in self.roots:
            for leaf in self.leafs:
                for path in nx.all_simple_paths(
                    self._graph, root.event_id, leaf.event_id
                ):
                    yield tuple(self[n] for n in path)

    @staticmethod
    def union(*log_graphs: "LogGraph") -> "LogGraph":
        new_log_graph = LogGraph()
        for log_graph in log_graphs:
            new_log_graph._graph.update(log_graph._graph)
            new_log_graph._loc.update(log_graph._loc)
        return new_log_graph

    @staticmethod
    def from_source(target_path: Path, launcher: str = "file") -> "LogGraph":
        log_graph = LogGraph()
        for (
            idom_id,
            event_id,
            path,
            package,
            class_name,
            method_name,
            line_number,
            level,
            template,
        ) in _extract_log_statements(target_path, launcher=launcher):
            event_id = int(event_id)
            idom_id = int(idom_id) if idom_id else None
            log_graph._graph.add_node(
                event_id,
                idom_id=idom_id,
                file_name=Path(path).name,
                line_number=int(line_number),
                level=level.upper(),
                template=template,
            )
            log_graph._graph.add_edge(event_id, idom_id)
        return log_graph

    @staticmethod
    def from_logs(logs: Sequence[Sequence[int]], min_support_ratio=0.05) -> "LogGraph":
        patterns = prefixspan(logs, minsup=int(len(logs) * min_support_ratio))
        return LogGraph.from_patterns(patterns)

    @staticmethod
    def from_patterns(
        ps: prefixspan,
    ) -> "LogGraph":
        log_graph = LogGraph()
        stack = [*ps]
        visited = set()
        while len(stack) > 0:
            i, t = stack.pop()
            visited.add(i)
            for j, s in t:
                log_graph._graph.add_edge(i, j)
        return log_graph

    def shortest_path(self, a: int, b: int) -> list[int]:
        return cast(list[int], nx.shortest_path(self._graph, a, b))


@dataclass(slots=True, frozen=True, eq=True)
class LogStatement:
    _graph: nx.DiGraph
    event_id: int

    @property
    def idom(self) -> "LogStatement | None":
        idom_id: int = self._graph.nodes[self.event_id]["idom_id"]
        if idom_id is None:
            return None
        return self._graph.nodes[idom_id]

    @property
    def level(self) -> str:
        return self._graph.nodes[self.event_id]["level"]

    @property
    def file_name(self) -> str:
        return self._graph.nodes[self.event_id]["file_name"]

    @property
    def line_number(self) -> int:
        return self._graph.nodes[self.event_id]["line_number"]

    @property
    def template(self) -> str:
        return self._graph.nodes[self.event_id]["template"]

    @property
    def loc(self):
        return (self.file_name, self.line_number)

    @property
    def dominators(self):
        node = self
        while node.idom:
            node = node.idom
            yield node

    @property
    def variables(self):
        return re.findall(r"\{(\w*)\}", self.template)


def _extract_log_statements(path: Path, launcher: str = "file") -> Iterator[list[str]]:
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
