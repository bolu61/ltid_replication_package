package sense.logid;

import java.util.EnumSet;
import java.util.Iterator;
import java.util.NoSuchElementException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

import fr.inria.controlflow.BranchKind;
import fr.inria.controlflow.ControlFlowBuilder;
import fr.inria.controlflow.ControlFlowGraph;
import fr.inria.controlflow.ControlFlowNode;
import fr.inria.controlflow.NaiveExceptionControlFlowStrategy;
import fr.inria.controlflow.NotFoundException;
import sense.logid.dominators.DominatorTree;
import sense.logid.dominators.ForwardFlowGraph;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtExecutable;

public class DominatorControlFlowGraph implements ForwardFlowGraph {
    Logger logger = LoggerFactory.getLogger(DominatorControlFlowGraph.class);

    public static class Factory {
        private Cache<CtExecutable<?>, DominatorControlFlowGraph> cache = Caffeine.newBuilder()
                .weakKeys()
                .softValues()
                .build();

        public DominatorControlFlowGraph get(CtExecutable<?> executable) {
            return cache.get(executable, DominatorControlFlowGraph::of);
        }
    }

    private final ControlFlowGraph graph;
    private DominatorTree tree;

    private DominatorControlFlowGraph(ControlFlowGraph graph) {
        this.graph = graph;
    }

    public static DominatorControlFlowGraph of(CtExecutable<?> method) {
        ControlFlowBuilder builder = new ControlFlowBuilder();

        EnumSet<NaiveExceptionControlFlowStrategy.Options> options;
        options = EnumSet.of(NaiveExceptionControlFlowStrategy.Options.ReturnWithoutFinalizers);

        builder.setExceptionControlFlowStrategy(new NaiveExceptionControlFlowStrategy(options));
        ControlFlowGraph graph = builder.build(method);
        return new DominatorControlFlowGraph(graph);
    }

    @Override
    public int size() {
        return graph.vertexSet().size();
    }

    @Override
    public int source() {
        var nodes = graph.findNodesOfKind(BranchKind.BEGIN);
        assert nodes.size() == 1;
        return nodes.get(0).getId();
    }

    @Override
    public int[] succ(int v) {
        return graph.findNodeById(v).next().stream().mapToInt(ControlFlowNode::getId).toArray();
    }

    CtElement idom(CtElement element) {
        if (tree == null) {
            tree = DominatorTree.snca(this);
        }

        ControlFlowNode out;

        try {
            out = graph.findNode(element);
        } catch (NotFoundException e) {
            return null;
        }

        do {
            var id = tree.parent(out.getId());
            if (id == -1) {
                return null;
            } else {
                out = graph.findNodeById(id);
            }
        } while (out.getStatement() == null);

        return out.getStatement();
    }

    public CtElement root() {
        var begin = graph.findNodesOfKind(BranchKind.BEGIN);
        assert begin.size() == 1;
        return begin.get(0).getStatement();
    }

    public Iterable<CtElement> dominators(CtElement element) {
        return () -> new DominatorIterator(element);
    }

    class DominatorIterator implements Iterator<CtElement> {
        private CtElement current;
        private CtElement next;

        DominatorIterator(CtElement element) {
            current = element;
            next = null;
        }
        
        private CtElement getNext() {
            if (next == null) {
                next = idom(current);
            }
            return next;
        }

        @Override
        public boolean hasNext() {
            return getNext() != null;
        }

        @Override
        public CtElement next() {
            current = getNext();
            if (current == null) {
                throw new NoSuchElementException();
            }
            next = null;
            return current;
        }
    }
}
