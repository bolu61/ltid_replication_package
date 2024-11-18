import csv
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Iterable

import networkx as nx

_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LTID_LOG_GRAPH_CLASSPATH = (
    resources.files((__package__ or "__main__").split(".")[0]) / "include" / "*"
)


def gather(path: Path, launcher: str = "file") -> Iterable["LogType"]:
    factory = LogTypeManager()
    out = _run_log_graph(path, "gather", launcher=launcher).splitlines()
    for row in csv.reader(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL):
        yield factory.make(*row)


def get_log_graph(path: Path, launcher: str = "file") -> nx.DiGraph:
    g = nx.DiGraph()
    for row in csv.reader(
        _run_log_graph(path, "output", launcher=launcher),
        delimiter=",",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    ):
        pass
    return g


def _run_log_graph(
    path: Path, command: str, *args: str, launcher: str = "file"
) -> Iterable[str]:
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

    def make(self, idom: str, event: str, level: str, template: str, package: str | None = None, path: str | None = None, parent: str | None = None, line: str | None = None):
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
