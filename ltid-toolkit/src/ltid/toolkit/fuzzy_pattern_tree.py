from collections.abc import Sequence


class SuffixTree[T]:
    """Generalized suffix tree for a set of sequences."""

    class Edge:
        sequence: Sequence[T]
        start: int
        end: int | None
        node: "SuffixTree.Node"

        def __init__(
            self,
            sequence: Sequence[T],
            offset: int,
            node: "SuffixTree.Node",
            end: int | None = None,
        ):
            self.sequence = sequence
            self.start = offset
            self.end = end
            self.node = node

        def at(self, i: int) -> T:
            return self.sequence[self.start + i]
    
        def ends_at(self, i: int) -> bool:
            return self.end == i

    class Node:
        edges: list["SuffixTree.Edge"]
        suffix_link: "SuffixTree.Node | None"

        def __init__(self):
            self.edges = []
            self.suffix_link = None

    _count = 0
    _root: Node
    _corpus: Sequence[Sequence[T]]

    def __init__(self, sequences: Sequence[Sequence[T]]):
        self._corpus = sequences
        self._root = SuffixTree.Node()
        for sequence in sequences:
            self._add_sequence(sequence)

    def _add_sequence(self, sequence: Sequence[T]):
        node: "SuffixTree.Node" = self._root
        edge: "SuffixTree.Edge | None" = None
        offset: int = 0
        remainder: int = 1
        for i, s in enumerate(sequence):
            if edge is None:
                n: "SuffixTree.Node | None" = node
                while n is not None:
                    self._add_edge(node, sequence, i)
                self._add_edge(node, sequence, i)
                break

            while remainder > 0:
                if edge.at(offset) == s:
                    offset += 1
                    remainder += 1
                    if edge.end == offset:
                        node = edge.node
                        edge = None
                    break
                
                self._split_edge(edge, offset)
                self._add_edge(edge.node, sequence, i)
                
                
                



    

    def _add_edge(self, node: "SuffixTree.Node", sequence: Sequence[T], offset: int):
        child = SuffixTree.Node()
        edge = SuffixTree.Edge(sequence, offset, child)
        node.edges.append(edge)
        return edge

    def _get_edge(self, node: "SuffixTree.Node", s: T) -> "SuffixTree.Edge | None":
        for edge in node.edges:
            if edge.at(0) == s:
                return edge
        return None

    def _split_edge(
        self, edge: "SuffixTree.Edge", offset: int
    ) -> "SuffixTree.Edge | None":
        assert edge.end == None or edge.end > edge.start + offset
        new_edge = SuffixTree.Edge(
            edge.sequence, edge.start + offset, edge.node, edge.end
        )
        edge.node = SuffixTree.Node()
        edge.node.edges.append(new_edge)
        edge.end = edge.start + offset


    def is_leaf(self, node: "SuffixTree.Node") -> bool:
        return len(node.edges) == 0
