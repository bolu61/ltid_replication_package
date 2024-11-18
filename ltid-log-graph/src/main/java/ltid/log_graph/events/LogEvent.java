package ltid.log_graph.events;

import java.util.Collection;
import java.util.Optional;

import ltid.log_graph.Variable;
import spoon.reflect.cu.SourcePosition;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtType;
import spoon.reflect.path.CtPath;

public interface LogEvent {

    public enum Level {
        FATAL, ERROR, WARN, INFO, DEBUG, TRACE, LOG
    }

    Optional<LogEvent> dominator();

    int id();

    CtElement getElement();

    CtPath path();

    Level level();

    String template();

    Collection<Variable> variables();

    default Optional<CtExecutable<?>> getExecutable() {
        return Optional.ofNullable(getElement().getParent(CtExecutable.class));
    }

    default Optional<CtMethod<?>> getMethod() {
        return getExecutable().filter(e -> e instanceof CtMethod<?>).map(m -> (CtMethod<?>) m);
    }

    @SuppressWarnings("unchecked")
    default CtType<?> getDeclaringType() {
        return getMethod().map(m -> m.getDeclaringType()).orElseGet(() -> getElement().getParent(CtType.class));
    }

    default SourcePosition getPosition() {
        return getElement().getPosition();
    }
}
