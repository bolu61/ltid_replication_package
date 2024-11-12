from subprocess import PIPE, run
from dataclasses import dataclass, field
from typing import Dict, Iterable, List
import csv
from pathlib import Path
import os
import re


_TEMPLATE_VAR_REGEX = re.compile(r"\{(\w*)\}")

LOGID_JAVA_SOURCEPATH = Path(__file__).parent.resolve() / "logid"
LOGID_JAVA_CLASSPATH = ["target/classes", "target/dependency/*"]


def mvn(*args: str) -> None:
    result = run(
        ["/usr/bin/env", "mvn", "--quiet", *args],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        cwd=LOGID_JAVA_SOURCEPATH,
    )
    if result.returncode != 0:
        raise MavenExecutionError(
            {
                "command": result.args,
                "returncode": result.returncode,
                "stderr": result.stderr,
                "stdout": result.stdout,
            }
        )


class MavenExecutionError(Exception):
    pass


mvn("compile")
mvn("dependency:copy-dependencies")


def gather(path: Path, launcher: str = "file") -> Iterable["LogType"]:
    factory = LogTypeFactory()
    out = logid(path, "gather", launcher=launcher).splitlines()
    for row in csv.reader(out, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL):
        yield factory.cons(*row)


def logid(path: Path, command: str, *args: str, launcher: str = "file"):
    result = run(
        [
            "java",
            "-cp",
            os.pathsep.join(LOGID_JAVA_CLASSPATH),
            "anana2.sense.logid.Launcher",
            "--environment",
            f"{launcher}:{path}",
            command,
            *args,
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        cwd=LOGID_JAVA_SOURCEPATH,
    )
    if result.returncode != 0:
        raise LogidExecutionError(
            {
                "command": result.args,
                "returncode": result.returncode,
                "message": result.stderr,
                "output": result.stdout,
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
