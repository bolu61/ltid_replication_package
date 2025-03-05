import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Iterator

from lxml import etree
from pygit2 import (
    Commit,
    Diff,
)
from pygit2.enums import DiffOption, SortMode
from pygit2.repository import Repository
from pylibsrcml.srcml import srcml_archive, srcml_unit

from .query import extract_id, extract_log

WALK_ORDER = SortMode.REVERSE | SortMode.TOPOLOGICAL | SortMode.TIME

DIFF_FLAGS = (
    DiffOption.INDENT_HEURISTIC
    | DiffOption.IGNORE_WHITESPACE_CHANGE
    | DiffOption.PATIENCE
    | DiffOption.MINIMAL
)


def walk(repository: Repository) -> Iterator[Commit]:
    for commit in repository.walk(repository.head.target, WALK_ORDER):
        yield commit


class ChangeType(Enum):
    OLD = "-"
    NEW = "+"
    REV = "~"


@dataclass(slots=True)
class DiffTrack:
    commit: str
    timestamp: int
    parents: int = 0
    numold: int = 0
    numoldid: int = 0
    numnew: int = 0
    numnewid: int = 0
    numrev: int = 0
    numrevid: int = 0

    @classmethod
    def fromcommit(cls, commit: Commit) -> "DiffTrack":
        return cls(str(commit.id), commit.commit_time)


class SourceParser:
    _archive: srcml_archive
    _xmlparser: etree.XMLParser

    def __init__(self, language: str):
        self._archive = srcml_archive()
        self._archive.set_language(language)

        self._xmlparser = etree.XMLParser(
            huge_tree=True,
            ns_clean=True,
            recover=True,
            encoding="utf-8",
        )

    def parsestring(self, code: str):
        unit = srcml_unit(self._archive)
        unit.parse_memory(code)

        srctree = unit.get_srcml()
        return etree.fromstring(srctree, parser=self._xmlparser)


class DiffTracker:
    _repository: Repository
    _parser: SourceParser

    def __init__(self, repository: Repository, parser: SourceParser):
        self._repository = repository
        self._parser = parser

    def track(self, commit: Commit) -> DiffTrack:
        track = DiffTrack.fromcommit(commit)
        for parent in commit.parents:
            diff = self._repository.diff(
                commit.id, parent.id, flags=DIFF_FLAGS, context_lines=4
            )
            if type(diff) is not Diff:
                raise Exception()
            for patch in diff:
                if patch.delta.is_binary or not patch.delta.new_file.path.endswith(
                    ".java"
                ):
                    continue
                for hunk in patch.hunks:
                    oldlines = []
                    newlines = []

                    for line in hunk.lines:
                        if line.origin in " -<=>":
                            oldlines.append(line)
                        if line.origin in " +<=>":
                            newlines.append(line)

                    for change, has_id in itertools.chain(
                        self.changedlogs(oldlines, "-"), self.changedlogs(newlines, "+")
                    ):
                        if change == "-":
                            track.numold += 1
                            if has_id:
                                track.numoldid += 1
                        if change == "+":
                            track.numnew += 1
                            if has_id:
                                track.numnewid += 1
                        if change == "~":
                            track.numrev += 1
                            if has_id:
                                track.numrevid += 1
        return track

    def changedlogs(self, lines, changetype):
        """find spans of changed logs"""
        out = []
        i = 0
        n = len(lines)
        count = 0
        content = ""
        changes = ""
        while i < n:
            line = lines[i]
            content += " " + line.content.strip()
            changes += line.origin
            count += line.content.count("(") - line.content.count(")")
            if count == 0:
                if changetype in changes:
                    root = self._parser.parsestring(content)
                    for stmt in extract_log(root):
                        if any(c != changetype for c in changes):
                            out.append(("~", len(list(extract_id(stmt))) != 0))
                        else:
                            out.append((changetype, len(list(extract_id(stmt))) != 0))
                content = ""
                changes = ""
            i += 1
        return out
