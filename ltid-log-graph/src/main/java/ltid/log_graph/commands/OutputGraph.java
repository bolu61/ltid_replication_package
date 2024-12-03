package ltid.log_graph.commands;

import java.io.IOException;
import java.io.Writer;
import java.util.function.Function;

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
        } catch (IOException e) {
            
        }
    }

    private String[] toRecord(LogEvent logEvent) {
        String dominator = String.valueOf(logEvent.dominator().map(d -> d.id()).orElse(-1));
        String logEventId = String.valueOf(logEvent.id());
        String path = logEvent.getPosition().getFile().getPath().toString();
        String packageName = logEvent.getDeclaringType().getQualifiedName();
        String className = logEvent.getDeclaringType().getQualifiedName();
        String methodName = logEvent.getExecutable().map(e -> e.getSimpleName()).orElse("<init>");
        String lineNumber = String.valueOf(logEvent.getPosition().getLine());
        String level = String.valueOf(logEvent.level());
        String template = logEvent.template();
        return new String[] {
                dominator,
                logEventId,
                path,
                packageName,
                className,
                methodName,
                lineNumber,
                level,
                template,
        };
    }
}
