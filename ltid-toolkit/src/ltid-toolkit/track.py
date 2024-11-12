from dataclasses import dataclass
from enum import Enum
import itertools
from typing import Iterator

from pygit2 import (
    Commit,
    Diff,
    GIT_DIFF_IGNORE_WHITESPACE_CHANGE,
    GIT_DIFF_INDENT_HEURISTIC,
    GIT_DIFF_MINIMAL,
    GIT_DIFF_PATIENCE,
    GIT_SORT_REVERSE,
    GIT_SORT_TIME,
    GIT_SORT_TOPOLOGICAL,
    Repository,
)

from .parse import Parser
from .query import extractid, extractlog

WALK_ORDER = GIT_SORT_REVERSE | GIT_SORT_TOPOLOGICAL | GIT_SORT_TIME

DIFF_FLAGS = (
    GIT_DIFF_INDENT_HEURISTIC
    | GIT_DIFF_IGNORE_WHITESPACE_CHANGE
    | GIT_DIFF_PATIENCE
    | GIT_DIFF_MINIMAL
)


def walk(repository: Repository) -> Iterator[Commit]:
    for commit in repository.walk(repository.head.target, WALK_ORDER):
        yield commit


class changetype(Enum):
    OLD = "-"
    NEW = "+"
    REV = "~"


@dataclass(slots=True)
class difftrack:
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
    def fromcommit(cls, commit: Commit) -> "difftrack":
        return cls(commit.id.hex, commit.commit_time)


class difftracker:
    _repository: Repository
    _parser: Parser

    def __init__(self, repository: Repository, parser: Parser):
        self._repository = repository
        self._parser = parser

    def track(self, commit: Commit) -> difftrack:
        track = difftrack.fromcommit(commit)
        for parent in commit.parents:
            diff = self._repository.diff(
                commit, parent, flags=DIFF_FLAGS, context_lines=4
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
                    for stmt in extractlog(root):
                        if any(c != changetype for c in changes):
                            out.append(("~", len(list(extractid(stmt))) != 0))
                        else:
                            out.append((changetype, len(list(extractid(stmt))) != 0))
                content = ""
                changes = ""
            i += 1
        return out
