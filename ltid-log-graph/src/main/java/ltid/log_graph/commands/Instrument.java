package sense.ltid_log_graph.commands;

import sense.ltid_log_graph.DominatorControlFlowGraph;
import sense.ltid_log_graph.Environment;
import sense.ltid_log_graph.events.factory.LogEventFactory;
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
        this.logEventFactory.stream(model.getRootPackage());
    }
    
    private void run() {
        
    }
    
}
