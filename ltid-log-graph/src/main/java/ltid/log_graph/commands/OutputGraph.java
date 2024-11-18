package ltid.log_graph.commands;

import java.io.IOException;
import java.io.Writer;

import com.opencsv.CSVWriter;

import ltid.log_graph.Environment;
import ltid.log_graph.events.LogEvent;
import ltid.log_graph.events.factory.LogEventFactory;
import spoon.reflect.CtModel;
import spoon.reflect.cu.SourcePosition;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtPackage;

public class OutputGraph {

    public static void run(Writer out, Environment env) {
        new OutputGraph(out, env).run();
    }

    private LogEventFactory logEventFactory = new LogEventFactory();

    private final CSVWriter writer;
    private final CtModel model;

    private OutputGraph(Writer out, Environment env) {
        this.writer = new CSVWriter(out);
        this.model = env.model();
    }

    private void run() {
        this.logEventFactory.stream(model.getRootPackage()).forEach((LogEvent logEvent) -> {
            SourcePosition position = logEvent.element().getPosition();
            CtMethod<?> method = logEvent.element().getParent(CtMethod.class);
            if (method == null) {
                return;
            }
            CtPackage pkg = method.getDeclaringType().getPackage();
            if (pkg == null) {
                return;
            }
            String logEventId = String.valueOf(logEvent.id());
            String dominator = String.valueOf(logEvent.dominator().map(d -> d.id()).orElse(-1));
            String packageName = pkg.getQualifiedName();
            String className = method.getDeclaringType().getSimpleName();
            String fileName = position.getFile().getName();
            String methodName = method.getSimpleName();
            String lineNumber = String.valueOf(position.getLine());
            writer.writeNext(new String[] { logEventId, dominator, packageName, className, fileName, methodName, lineNumber });
        });
    }
}
