package ltid.log_graph.commands;

import java.io.Flushable;
import java.io.IOException;
import java.io.Writer;

import com.opencsv.CSVWriter;

import ltid.log_graph.events.LogEvent;
import ltid.log_graph.events.factory.LogEventFactory;
import spoon.reflect.CtModel;

public class Gather {
    static class GatherException extends RuntimeException {
        private GatherException(Throwable cause) {
            super(cause);
        }
    }

    public static void execute(Writer out, CtModel model) {
        LogEventWriter writer = new CSVLogEventWriter(out);

        LogEventFactory factory = new LogEventFactory();

        factory.stream(model.getRootPackage()).forEach(writer::write);

        try {
            writer.close();
        } catch (Exception e) {
            throw new GatherException(e);
        }
    }

    private interface LogEventWriter extends Flushable, AutoCloseable {
        void write(LogEvent event);
    }

    private static class CSVLogEventWriter implements LogEventWriter {
        CSVWriter delegate;

        CSVLogEventWriter(Writer out) {
            delegate = new CSVWriter(out);
        }

        public void write(LogEvent event) {
            delegate.writeNext(new String[] {
                    event.dominator().map(d -> String.valueOf(d.id())).orElse(""),
                    String.valueOf(event.id()),
                    String.valueOf(event.level()),
                    String.valueOf(event.template())
            });
        }

        @Override
        public void close() throws IOException {
            delegate.close();
        }

        @Override
        public void flush() throws IOException {
            delegate.flush();
        }
    }
}
