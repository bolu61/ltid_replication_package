import csv
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Iterable, Iterator, Any
from collections.abc import Mapping

import networkx as nx

_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LTID_LOG_GRAPH_CLASSPATH = (
    resources.files((__package__ or "__main__").split(".")[0]) / "include" / "*"
)


class LogGraph:
    _graph: nx.DiGraph

    def __init__(self):
        self._graph = nx.DiGraph()

    def add(
        self,
        idom_id: int,
        event_id: int,
        path: Path,
        package: list[str],
        class_name: str,
        method_name: str,
        line_number: int,
        level: str,
        template: str,
    ):
        node = LogNode(
            self._graph,
            id=event_id,
            path=path,
            package_name=package,
            class_name=class_name,
            method_name=method_name,
            line_number=line_number,
            level=level,
            template=template,
        )

        self._graph.add_node(event_id, log_statement=node)
        if idom_id >= 0:
            self._graph.add_edge(event_id, idom_id)

        return node

    def __getitem__(self, event_id: int):
        return self._graph.nodes[event_id]
    
    def dump(self) -> Mapping[Any, Any]:
        return nx.node_link_data(self._graph, link="edges")


@dataclass(slots=True)
class LogNode:
    _log_graph: nx.DiGraph
    id: int
    path: Path
    package_name: list[str]
    class_name: str
    method_name: str
    line_number: int
    level: str
    template: str

    @property
    def immediate_dominator(self):
        return next(self.dominators)

    @property
    def dominators(self):
        while len(nodes := self._log_graph.succ[self.id]) > 0:
            assert len(nodes) == 1
            yield (self := nodes[0])

    @property
    def variables(self):
        return _TEMPLATE_VAR_REGEX.findall(self.template)


def get_log_graph(target_path: Path, launcher: str = "file") -> LogGraph:
    log_graph = LogGraph()
    for (
        idom_id,
        event_id,
        path,
        package_name,
        class_name,
        method_name,
        line_number,
        level,
        template,
    ) in csv.reader(
        _run_log_graph(target_path, "output", launcher=launcher),
        delimiter=",",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    ):
        log_graph.add(
            idom_id=int(idom_id),
            event_id=int(event_id),
            path=Path(path),
            package=package_name.split("."),
            class_name=class_name,
            method_name=method_name,
            line_number=int(line_number),
            level=level,
            template=template,
        )

    return log_graph


def _run_log_graph(
    path: Path, command: str, *args: str, launcher: str = "file"
) -> Iterator[str]:
    proc = Popen(
        [
            "java",
            "-cp",
            str(LTID_LOG_GRAPH_CLASSPATH),
            "ltid.log_graph.Launcher",
            "--environment",
            f"{launcher}:{path}",
            command,
            *args,
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    assert proc.stdout is not None
    assert proc.stderr is not None
    yield from proc.stdout
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


class LogTypeManager:
    types: dict[int, "LogType"]

    def __init__(self):
        self.types = dict()

    def make(
        self,
        idom: str,
        event: str,
        level: str,
        template: str,
        package: str | None = None,
        path: str | None = None,
        parent: str | None = None,
        line: str | None = None,
    ):
        event_id = int(event)
        logtype = LogType(
            _manager=self,
            idom=int(idom),
            event=event_id,
            level=level.upper(),
            template=template,
        )

        self.types[event_id] = logtype

        return logtype

    def __getitem__(self, index: int):
        return self.types[index]


@dataclass(slots=True)
class LogType:
    _manager: LogTypeManager = field(repr=False)
    idom: int
    event: int
    level: str
    template: str
    package: list[str] | None = None
    path: Path | None = None
    parent: str | None = None
    lineno: int | None = None

    @property
    def dominators(self):
        node = self
        while node.idom:
            node = self._manager[node.idom]
            yield node

    @property
    def variables(self):
        return _TEMPLATE_VAR_REGEX.findall(self.template)


def gather(path: Path, launcher: str = "file") -> Iterable["LogType"]:
    factory = LogTypeManager()
    out = _run_log_graph(path, "gather", launcher=launcher)
    for row in csv.reader(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL):
        yield factory.make(*row)
