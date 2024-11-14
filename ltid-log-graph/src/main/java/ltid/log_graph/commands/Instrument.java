package ltid.log_graph.commands;

import ltid.log_graph.DominatorControlFlowGraph;
import ltid.log_graph.Environment;
import ltid.log_graph.events.factory.LogEventFactory;
import spoon.reflect.CtModel;

public class Instrument {
    
    public static void run(Environment env) {
        new Instrument(env).run();
    }
    
    private LogEventFactory logEventFactory = new LogEventFactory();
    private DominatorControlFlowGraph.Factory cfgFactory = new DominatorControlFlowGraph.Factory();
    
    private final CtModel model;
    
    private Instrument(Environment env) {
        this.model = env.model(); 
    }
    
    private void run() {
        this.logEventFactory.stream(model.getRootPackage());
    }
    
}
