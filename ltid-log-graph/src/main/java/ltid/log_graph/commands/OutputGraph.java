package ltid.log_graph.commands;

import java.io.IOException;
import java.io.Writer;

import com.opencsv.CSVWriter;

import ltid.log_graph.Environment;
import ltid.log_graph.events.LogEvent;
import ltid.log_graph.events.factory.LogEventFactory;

public class OutputGraph {

    public static void run(Writer out, Environment env) throws IOException {
        new OutputGraph(out, env).run();
    }

    private final Writer out;
    private final Environment env;

    private OutputGraph(Writer out, Environment env) {
        this.out = out;
        this.env = env;
    }

    private void run() throws IOException {
        try (CSVWriter writer = new CSVWriter(out)) {
            new LogEventFactory().stream(env.rootPackage())
                    .map(this::toRecord)
                    .forEach(writer::writeNext);
        }
    }

    private String[] toRecord(LogEvent logEvent) {
        String dominator = String.valueOf(logEvent.dominator().map(d -> d.id()).orElse(-1));
        String logEventId = String.valueOf(logEvent.id());
        String className = logEvent.getDeclaringType().getQualifiedName();
        String fileName = logEvent.getPosition().getFile().getName();
        String methodName = logEvent.getExecutable().map(e -> e.getSimpleName()).orElse("<init>");
        String lineNumber = String.valueOf(logEvent.getPosition().getLine());
        String level = String.valueOf(logEvent.level());
        String template = logEvent.template();
        String variables = String.valueOf(logEvent.variables());
        return new String[] {
                dominator,
                logEventId,
                className,
                fileName,
                methodName,
                lineNumber,
                level,
                template,
                variables
        };
    }
}
