import csv
import json
import re
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from importlib import resources
from io import StringIO
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Iterable, Iterator, Sequence, TextIO
from ltid.toolkit.separate import separate
from prefixspan import make_trie, trie

import networkx as nx

_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LTID_LOG_GRAPH_CLASSPATH = (
    resources.files((__package__ or "__main__").split(".")[0]) / "include" / "*"
)


class JSONEncoderWithPath(json.JSONEncoder):
    def default(self, o: Any):
        match o:
            case Path():
                return str(o)
            case _:
                return super().default(o)


@dataclass
class GetLogGraphArguments(Namespace):
    file: Path | None = None


def main():
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        "-f",
        "--file",
        type=Path,
        required=True,
    )
    arguments = argument_parser.parse_args(namespace=GetLogGraphArguments())
    match arguments:
        case GetLogGraphArguments(file) if file is not None:
            log_graph = LogGraph.from_source(file, launcher="file")
        case _:
            raise NotImplementedError()

    log_graph.dump(sys.stdout)


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
        self._graph.add_node(
            event_id,
            id=event_id,
            path=path,
            package_name=package,
            class_name=class_name,
            method_name=method_name,
            line_number=line_number,
            level=level,
            template=template,
        )

        if idom_id >= 0:
            self._graph.add_edge(event_id, idom_id)

    def __getitem__(self, event_id: int):
        return self._graph.nodes[event_id]

    def __str__(self) -> str:
        with StringIO() as buf:
            self.dump(buf)
            return buf.getvalue()

    def dump(self, file: TextIO):
        data = nx.node_link_data(self._graph, link="edges")
        json.dump(data, file, cls=JSONEncoderWithPath)
        
    @staticmethod
    def from_logs(logs: Sequence[str]) -> "LogGraph":
        log_graph = LogGraph()
        pattern_tree = make_trie(logs, minsup = len(logs) // 10)
        return log_graph

    @staticmethod
    def from_source(target_path: Path, launcher: str = "file") -> "LogGraph":
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


if __name__ == "__main__":
    main()
