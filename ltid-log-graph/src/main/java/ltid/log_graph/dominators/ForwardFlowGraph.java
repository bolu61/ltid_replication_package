package ltid.log_graph.dominators;

public interface ForwardFlowGraph {
    int source();

    int size();

    int[] succ(int v);
}
