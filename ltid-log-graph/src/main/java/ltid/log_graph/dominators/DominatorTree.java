package ltid.log_graph.dominators;

public interface DominatorTree {
    int size();

    int root();

    int parent(int u);

    public static DominatorTree snca(ForwardFlowGraph graph) {
        return SNCADominatorTree.from(graph);
    }
}
