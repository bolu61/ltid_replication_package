package sense.logid.utilities;

import java.util.EnumSet;
import java.util.Iterator;

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
import sense.intgraph.FlowGraph;
import sense.intgraph.ParentTree;
import sense.intgraph.algo.DominatorTrees;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtExecutable;

public class CFG implements FlowGraph {
    Logger logger = LoggerFactory.getLogger(CFG.class);

    public static class Factory {
        private Cache<CtExecutable<?>, CFG> cache = Caffeine.newBuilder()
                .weakKeys()
                .softValues()
                .build();

        public CFG get(CtExecutable<?> executable) {
            return cache.get(executable, CFG::of);
        }
    }

    private final ControlFlowGraph graph;
    private ParentTree tree;

    private CFG(ControlFlowGraph graph) {
        this.graph = graph;
    }

    public static CFG of(CtExecutable<?> method) {
        ControlFlowBuilder builder = new ControlFlowBuilder();

        EnumSet<NaiveExceptionControlFlowStrategy.Options> options;
        options = EnumSet.of(NaiveExceptionControlFlowStrategy.Options.ReturnWithoutFinalizers);

        builder.setExceptionControlFlowStrategy(new NaiveExceptionControlFlowStrategy(options));
        ControlFlowGraph graph = builder.build(method);
        return new CFG(graph);
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
            tree = DominatorTrees.snca(this);
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

        @Override
        public boolean hasNext() {
            next = idom(current);
            return next != null;
        }

        @Override
        public CtElement next() {
            if (next == null) {
                next = idom(current);
            }
            if (next == null) {
                throw new IllegalStateException();
            }
            current = next;
            next = null;
            return current;
        }
    }
}
