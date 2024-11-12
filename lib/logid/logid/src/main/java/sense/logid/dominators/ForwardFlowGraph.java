package sense.logid.dominators;

public interface ForwardFlowGraph {
    int source();

    int size();

    int[] succ(int v);
}
