package sense.ltid_log_graph.commands;

import java.io.IOException;
import java.io.Writer;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.opencsv.CSVWriter;

import sense.ltid_log_graph.Environment;
import sense.ltid_log_graph.Variable;
import sense.ltid_log_graph.events.LogEvent;
import sense.ltid_log_graph.events.factory.LogEventFactory;
import sense.ltid_log_graph.fragments.ElementLocator;
import sense.ltid_log_graph.fragments.FragmentList;
import spoon.reflect.declaration.CtExecutable;

public class Injections {
    private static final Logger logger = LoggerFactory.getLogger(Injections.class);

    private Injections() {
    }

    public static void execute(Writer out, Environment env, Optional<String[]> ids) {
        var model = env.model();
        var printer = new CSVWriter(out);
        var factory = new LogEventFactory();

        final Set<String> idx;
        final boolean shouldFilter;
        if (ids.isPresent()) {
            shouldFilter = true;
            idx = new HashSet<>(Arrays.asList(ids.get()));
        } else {
            shouldFilter = false;
            idx = null;
        }

        StreamSupport.stream(model.getRootPackage().asIterable().spliterator(), false)
                .filter(e -> e instanceof CtExecutable<?>)
                .forEach(executable -> {
                    factory.stream(executable).forEach(event -> {
                        if (logger.isTraceEnabled()) {
                            logger.trace("Found event {}.", event);
                        }

                        if (event.dominator().isEmpty()) {
                            if (logger.isTraceEnabled()) {
                                logger.trace("No dominator found for event {}.", event);
                            }
                            return;
                        }

                        var dominator = event.dominator();
                        var acc = acc(dominator.get());
                        if (shouldFilter) {
                            acc = acc.filter(variable -> idx.contains(variable.name()));
                        }

                        var variables = new HashSet<>(event.variables());

                        acc = acc.filter(variable -> !variables.contains(variable));

                        var injected = acc.toList();

                        if (injected.isEmpty()) {
                            if (logger.isTraceEnabled()) {
                                logger.trace("No injected variable found for event {}.", event);
                            }
                            return;
                        }

                        var element = event.element();

                        var sniper = new ElementLocator(executable);

                        var fragment = blockresize(sniper.locate(), sniper.locate(executable));

                        var lines = fragment.split(System.lineSeparator());

                        var indentation = lines.stream().flatMap(piece -> {
                            var line = piece.toString();
                            var i = indentation(line);
                            if (line.length() == i) {
                                return Stream.empty();
                            }
                            return Stream.of(i);
                        }).min(Comparator.naturalOrder()).orElse(0);

                        lines.forEach(piece -> {
                            piece.delete(piece.head(), indentation);
                        });

                        // build log id injection comments
                        var msg = new StringBuilder();
                        msg.append(String.format("/* #LOG %s %s%n", event.level(), event.template()));
                        msg.append(" *" + System.lineSeparator());
                        for (var variable : injected) {
                            msg.append(String.format(" * %s: %s%n", variable.name(),
                                    sniper.locate(variable.element()).toString()));
                        }
                        msg.append(" */");

                        comment(blockresize(fragment, sniper.locate(element)), msg.toString());
                        while (dominator.isPresent()) {
                            comment(blockresize(fragment, sniper.locate(dominator.get().element())),
                                    "// #LOG ASSOCIATE");
                            dominator = dominator.get().dominator();
                        }

                        printer.writeNext(new String[] {
                                fragment.toString()
                        });
                    });
                });
        try {
            printer.close();
        } catch (IOException e) {
            logger.error("while closing csv printer", e);
        }
    }

    private static void comment(FragmentList fragment, String string) {
        var indentation = " ".repeat(indentation(fragment.toString()));
        fragment.insert(fragment.head(), System.lineSeparator());
        var comment = fragment.insert(fragment.head(), string);
        for (var line : comment.split(System.lineSeparator())) {
            line.insert(line.head(), indentation);
        }
    }

    private static int indentation(String string) {
        var i = 0;
        while (i < string.length() && Character.isWhitespace(string.charAt(i))) {
            i++;
        }
        return i;
    }

    private static Stream<Variable> acc(LogEvent log) {
        var variables = log.variables().stream();
        return log.dominator().map(dominator -> {
            return Stream.concat(variables, acc(dominator));
        }).orElse(variables);
    }

    static FragmentList blockresize(FragmentList ctx, FragmentList element) {
        var fragment = ctx.head().range(element.head());

        var source = fragment.toString();

        var offset = source.length();

        while (offset > 0 && (source.codePointAt(offset - 1) == ' ' || source.codePointAt(offset - 1) == '\t')) {
            offset--;
        }

        return fragment.at(offset).range(element.last());
    }
}
