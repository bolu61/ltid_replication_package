import csv
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from subprocess import PIPE, run
from typing import Annotated, Iterable

_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LTID_LOG_GRAPH_CLASSPATH = resources.files(__package__.split(".")[0]) / "include" / "*"


def gather(path: Path, launcher: str = "file") -> Iterable["LogType"]:
    factory = LogTypeManager()
    out = _run_log_graph(path, "gather", launcher=launcher).splitlines()
    for row in csv.reader(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL):
        yield factory.make(*row)


def _run_log_graph(path: Path, command: str, *args: str, launcher: str = "file"):
    result = run(
        [
            "java",
            "-cp",
            LTID_LOG_GRAPH_CLASSPATH,
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
    if result.returncode != 0:
        raise LTIDLogGraphExecutionError(
            {
                "command": result.args,
                "returncode": result.returncode,
                "message": result.stderr,
                "output": result.stdout,
                "classpath": LTID_LOG_GRAPH_CLASSPATH,
            }
        )
    return result.stdout


class LTIDLogGraphExecutionError(Exception):
    pass


class LogTypeManager:
    types: dict[str, "LogType"]

    def __init__(self):
        self.types = dict()

    def make(self, idom: str, event: str, level: str, template: str):
        logtype = LogType(
            _manager=self,
            idom=idom,
            level=level.upper(),
            template=template,
        )

        self.types[event] = logtype

        return logtype

    def __getitem__(self, index: str):
        return self.types[index]


@dataclass(slots=True)
class LogType:
    _manager: Annotated[LogTypeManager, field(repr=False)]
    idom: str
    event: str
    level: str
    template: str

    @property
    def dominators(self):
        node = self
        while node.idom:
            node = self._manager[node.idom]
            yield node

    @property
    def variables(self):
        return _TEMPLATE_VAR_REGEX.findall(self.template)
