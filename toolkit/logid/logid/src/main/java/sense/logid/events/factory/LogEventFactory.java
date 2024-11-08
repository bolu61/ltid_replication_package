package sense.logid.events.factory;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

import sense.logid.Counter;
import sense.logid.DominatorControlFlowGraph;
import sense.logid.Variable;
import sense.logid.events.LogEvent;
import sense.logid.events.LogEvent.Level;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.path.CtPath;
import spoon.reflect.path.CtPathException;

public class LogEventFactory {
    private static final Logger logger = LoggerFactory.getLogger(LogEventFactory.class);
    private static final Pattern LOG_FORMAT_PATTERN = Pattern.compile("(?<!\\\\)\\\\\\{\\\\\\}");

    private DominatorControlFlowGraph.Factory graphFactory = new DominatorControlFlowGraph.Factory();

    private Cache<CtElement, Optional<LogEvent>> cache = Caffeine.newBuilder()
            .weakKeys()
            .softValues()
            .build();

    private Iterator<Integer> counter = new Counter().iterator();

    public Stream<LogEvent> stream(CtElement root) {
        var factory = new LogEventFactory();

        var elements = root.asIterable().spliterator();
        return StreamSupport.stream(elements, false)
                .flatMap(e -> factory.get(e).stream());
    }

    public Optional<LogEvent> get(CtElement element) {
        return cache.get(element, this::trycreate);
    }

    /**
     * Construct a log event from an invocation statement.
     *
     * @param element the invocation statement
     * @return the constructed log event
     */
    private Optional<LogEvent> trycreate(CtElement element) {
        try {
            if (!(element instanceof CtInvocation<?>)) {
                return Optional.empty();
            }

            if (logger.isTraceEnabled()) {
                logger.trace("Found invocation {}.", element.toStringDebug());
            }

            CtInvocation<?> invocation = (CtInvocation<?>) element;

            CtExpression<?> target = invocation.getTarget();

            if (target == null || !target.toStringDebug().toLowerCase().contains("log")) {
                return Optional.empty();
            }

            Level level;

            try {
                level = Level.valueOf(invocation.getExecutable().getSimpleName().toUpperCase());
            } catch (IllegalArgumentException e) {
                if (logger.isTraceEnabled()) {
                    logger.trace("Invocation {} isn't a logging method.", element.toStringDebug());
                }
                return Optional.empty();
            }

            List<CtExpression<?>> arguments = new ArrayList<>(invocation.getArguments());

            if (arguments.isEmpty()) {
                if (logger.isTraceEnabled()) {
                    logger.trace("Invocation {} is empty.", element.toStringDebug());
                }
                return Optional.empty();
            }

            String template;
            TemplateFactory templateFactory = new TemplateFactory();

            if (arguments.size() > 1) {
                CtExpression<?> format = templateFactory.discard(arguments);
                if (format == null) {
                    if (logger.isTraceEnabled()) {
                        logger.trace("Invocation {} no format string found.", element.toStringDebug());
                    }
                    return Optional.empty();
                }

                template = templateFactory.template(format, LOG_FORMAT_PATTERN, arguments);
            } else {
                template = templateFactory.template(arguments.get(0));
            }

            var dominator = dominator(element);
            var id = counter.next();

            return Optional.of(new LogEvent() {

                @Override
                public Optional<LogEvent> dominator() {
                    return dominator;
                }

                @Override
                public int id() {
                    return id;
                }

                @Override
                public CtElement element() {
                    return element;
                }

                @Override
                public Optional<CtPath> path() {
                    try {
                        return Optional.of(element.getPath());
                    } catch (CtPathException e) {
                        return Optional.empty();
                    }
                }

                @Override
                public Level level() {
                    return level;
                }

                @Override
                public String template() {
                    return template;
                }

                @Override
                public Collection<Variable> variables() {
                    return templateFactory.variables();
                }

                @Override
                public String toString() {
                    return String.format("\"%s\"", this.template());
                }
            });

        } catch (RuntimeException e) {
            return Optional.empty();
        }
    }

    private Optional<LogEvent> dominator(CtElement element) {
        Optional<LogEvent> dominator = Optional.empty();
        CtExecutable<?> executable = element.getParent(CtExecutable.class);
        // the log can be stated in a static initializer / implicit constructor
        if (executable != null) {
            DominatorControlFlowGraph graph = graphFactory.get(executable);
            // find youngest dominator that is an event
            for (CtElement dominating_element : graph.dominators(element)) {
                dominator = get(dominating_element);
                if (dominator.isPresent()) {
                    break;
                }
            }
        }

        return dominator;
    }
}