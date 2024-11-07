package sense.intgraph.algo;

import sense.intgraph.FlowGraph;
import sense.intgraph.ParentTree;

public interface DominatorTrees extends ParentTree {
    public static ParentTree snca(FlowGraph graph) {
        return SNCADominatorTree.from(graph);
    }
}
