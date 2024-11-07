package sense.intgraph;

public interface ModifiableGraph extends Graph {
    boolean add(int u, int v);

    boolean remove(int u, int v);
}
