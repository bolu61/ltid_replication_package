package anana2.sense.intgraph.algo;

import anana2.sense.intgraph.FlowGraph;
import anana2.sense.intgraph.ParentTree;

public interface DominatorTrees extends ParentTree {
    public static ParentTree snca(FlowGraph graph) {
        return SNCADominatorTree.from(graph);
    }
}
