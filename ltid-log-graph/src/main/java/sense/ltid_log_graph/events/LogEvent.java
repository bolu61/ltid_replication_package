package sense.ltid_log_graph.events;

import java.util.Collection;
import java.util.Optional;

import sense.ltid_log_graph.Variable;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.path.CtPath;

public interface LogEvent {

    public enum Level {
        FATAL, ERROR, WARN, INFO, DEBUG, TRACE, LOG
    }

    Optional<LogEvent> dominator();

    int id();

    CtElement element();

    CtPath path();

    Level level();

    String template();

    Collection<Variable> variables();
}
