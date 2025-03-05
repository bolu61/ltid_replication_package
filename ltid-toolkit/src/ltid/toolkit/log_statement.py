import networkx as nx


import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True, eq=True)
class LogStatement:
    _graph: nx.DiGraph
    event_id: int

    @property
    def idom(self) -> "LogStatement | None":
        successors = self._graph.successors(self.event_id)
        try:
            return LogStatement(self._graph, next(successors))
        except StopIteration:
            return None

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