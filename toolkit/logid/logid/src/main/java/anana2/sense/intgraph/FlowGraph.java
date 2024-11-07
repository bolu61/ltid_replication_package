package anana2.sense.intgraph;

public interface FlowGraph extends Graph {
    int source();

    int[] succ(int v);
}
