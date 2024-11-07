package anana2.sense.intgraph;

public interface ModifiableReverseFlowGraph extends ReverseFlowGraph, ModifiableGraph {
    int[] pred(int v);
}
