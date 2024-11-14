import csv
import os
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from subprocess import PIPE, run
from typing import Dict, Iterable, List

_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LTID_LOG_GRAPH_CLASSPATH = resources.files(__package__) / "include" / "*"


def gather(path: Path, launcher: str = "file") -> Iterable["LogType"]:
    factory = LogTypeFactory()
    out = _run_log_graph(path, "gather", launcher=launcher).splitlines()
    for row in csv.reader(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL):
        yield factory.cons(*row)


def _run_log_graph(path: Path, command: str, *args: str, launcher: str = "file"):
    result = run(
        [
            "java",
            "-cp",
            LTID_LOG_GRAPH_CLASSPATH,
            "sense.ltid_log_graph.Launcher",
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
        raise LogidExecutionError(
            {
                "command": result.args,
                "returncode": result.returncode,
                "message": result.stderr,
                "output": result.stdout,
<<<<<<< Updated upstream:ltid-toolkit/src/ltid_toolkit/log_graph.py
                "classpath": LTID_LOG_GRAPH_CLASSPATH,
=======
>>>>>>> Stashed changes:toolkit/logid/__init__.py
            }
        )
    return result.stdout


class LogidExecutionError(Exception):
    pass


class LogTypeFactory:
    types: Dict[str, "LogType"]

    def __init__(self):
        self.types = dict()

    def cons(self, idom: str, event: str, level: str, template: str):
        logtype = LogType(
            factory=self,
            idom=idom,
            level=level.upper(),
            template=template,
            variables=_TEMPLATE_VAR_REGEX.findall(template),
        )

        self.types[event] = logtype

        return logtype

    def find(self, index: str):
        return self.types[index]


@dataclass(slots=True)
class LogType:
    factory: LogTypeFactory = field(repr=False)
    idom: str = field(repr=False)
    level: str
    template: str
    variables: List[str]

    @property
    def dominators(self):
        node = self
        while node.idom:
            node = self.factory.find(node.idom)
            yield node
