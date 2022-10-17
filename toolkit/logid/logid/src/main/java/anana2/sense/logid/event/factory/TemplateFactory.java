package anana2.sense.logid.event.factory;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;

import anana2.sense.logid.Variable;
import spoon.reflect.code.BinaryOperatorKind;
import spoon.reflect.code.CtBinaryOperator;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.code.CtLiteral;
import spoon.reflect.code.CtNewArray;
import spoon.reflect.code.CtTypeAccess;
import spoon.reflect.code.CtVariableAccess;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtVariable;
import spoon.reflect.reference.CtArrayTypeReference;
import spoon.reflect.reference.CtExecutableReference;
import spoon.reflect.reference.CtReference;
import spoon.reflect.reference.CtTypeReference;
import spoon.reflect.reference.CtVariableReference;

class TemplateFactory {
    private static final String STRING_TYPE = "java.lang.String";
    static final Pattern STRING_FORMAT_PATTERN = Pattern.compile("(?<!\\\\)%\\S+");

    private final List<Variable> variables;

    TemplateFactory() {
        variables = new ArrayList<>();
    }

    public String variable(CtElement element) {
        var name = name(element);
        var id = variables.size();

        if (name.isEmpty()) {
            variables.add(new Variable() {
                @Override
                public String name() {
                    return "";
                }

                @Override
                public int id() {
                    return id;
                }

                @Override
                public CtElement element() {
                    return element;
                }
            });

            return String.format("{var%d}", id);
        } else {
            variables.add(new Variable() {
                @Override
                public String name() {
                    return name;
                }

                @Override
                public int id() {
                    return id;
                }

                @Override
                public CtElement element() {
                    return element;
                }
            });

            return String.format("{%s%d}", name, id);
        }
    }

    private String name(CtElement element) {
        // todo put implementation here
        return collect(element).replaceAll("(.{2,})(?:\\1)+", "$1");
    }

    public List<Variable> variables() {
        return Collections.unmodifiableList(variables);
    }

    public String template(CtExpression<?> format, Pattern pattern, List<CtExpression<?>> expressions) {
        String formatString = template(format);

        if (expressions.isEmpty()) {
            return formatString;
        }

        List<String> pieces = new ArrayList<>();
        Iterator<CtExpression<?>> iterator = expressions.iterator();
        Matcher matcher = null;
        while (true) {
            matcher = pattern.matcher(formatString);
            if (!iterator.hasNext() || !matcher.find()) {
                break;
            }
            pieces.add(formatString.substring(0, matcher.start()));
            pieces.add(template(iterator.next()));
            formatString = formatString.substring(matcher.end());
        }
        pieces.add(formatString);

        return String.join("", pieces);
    }

    String template(CtExpression<?> expression) {

        // compile format invocation
        if (expression instanceof CtInvocation) {
            CtInvocation<?> invocation = (CtInvocation<?>) expression;
            List<CtExpression<?>> arguments = invocation
                    .getArguments();
            CtExpression<?> target = invocation.getTarget();

            if (target instanceof CtTypeAccess
                    && ((CtTypeAccess<?>) target).getAccessedType()
                            .getQualifiedName()
                            .equals(STRING_TYPE)) {
                String signature = invocation.getExecutable()
                        .getSignature();
                if (signature.equals("format(java.lang.String,java.lang.Object[])")) {
                    if (arguments.size() == 2 && (arguments.get(1).getType() instanceof CtArrayTypeReference<?>)) {
                        if ((arguments.get(1) instanceof CtNewArray)) {
                            var array = (CtNewArray<?>) arguments.get(1);
                            return template(arguments.get(0), STRING_FORMAT_PATTERN, array.getElements());
                        }
                        return template(arguments.get(1));
                    }
                    return template(arguments.get(0), STRING_FORMAT_PATTERN, arguments);
                }
                if (signature.equals("format(java.util.Locale,java.lang.String,java.lang.Object[])")) {
                    if (arguments.size() == 3 && (arguments.get(2).getType() instanceof CtArrayTypeReference<?>)) {
                        if ((arguments.get(2) instanceof CtNewArray)) {
                            var array = (CtNewArray<?>) arguments.get(2);
                            return template(arguments.get(0), STRING_FORMAT_PATTERN, array.getElements());
                        }
                        return template(arguments.get(2));
                    }
                    return template(arguments.get(1), STRING_FORMAT_PATTERN,
                            arguments.subList(2, arguments.size()));
                }
            }

            if (target instanceof CtExpression
                    && target.getType() != null
                    && target.getType().getQualifiedName()
                            .equals(STRING_TYPE)) {
                String signature = invocation.getExecutable()
                        .getSignature();
                if (signature
                        .equals("concat(java.lang.String)")) {
                    return template(target) + template(arguments.get(0));
                }
            }
        }

        if (expression instanceof CtBinaryOperator<?>) {
            CtBinaryOperator<?> operation = (CtBinaryOperator<?>) expression;
            if (operation.getKind().equals(BinaryOperatorKind.PLUS)) {
                var left = operation.getLeftHandOperand();
                var right = operation.getRightHandOperand();
                return template(left) + template(right);
            }
        }

        if (expression instanceof CtVariableAccess) {
            CtVariableAccess<?> access = (CtVariableAccess<?>) expression;
            CtVariable<?> variable = access.getVariable()
                    .getDeclaration();

            if (variable != null && variable.isFinal() && variable.getType() != null && variable.getType().getQualifiedName().equals(STRING_TYPE)) {
                CtExpression<?> defaultExpression = variable.getDefaultExpression();
                if (defaultExpression != null && defaultExpression instanceof CtLiteral<?>) {
                    Object object = ((CtLiteral<?>) defaultExpression).getValue();
                    if (object == null) {
                      return "null";
                    }

                    return escape(object.toString());
                }
            }
        }

        if (expression instanceof CtLiteral<?>) {
            Object object = ((CtLiteral<?>) expression)
                    .getValue();
            if (object == null) {
                return "null";
            }

            return escape(object.toString());
        }

        // compile other cases
        return variable(expression);
    }

    CtExpression<?> discard(List<CtExpression<?>> arguments) {
        while (!arguments.isEmpty()) {
            CtExpression<?> expression = arguments.remove(0);
            CtTypeReference<?> type = expression.getType();
            if (type != null && type.getQualifiedName().equals(STRING_TYPE)) {
                return expression;
            }
        }
        return null;
    }

    static String collect(CtElement element) {
        return StreamSupport
                .stream(element.asIterable().spliterator(), false)
                .map(e -> {
                    if (e instanceof CtVariableReference
                            || e instanceof CtExecutableReference) {
                        String name = ((CtReference) e)
                                .getSimpleName();
                        return name(name);
                    }
                    if (e instanceof CtLiteral) {
                        Object object = ((CtLiteral<?>) e).getValue();
                        if (object == null) {
                            return "";
                        }
                        return name(object.toString());
                    }
                    return "";
                }).collect(Collectors.joining(""));
    }

    private static String name(String str) {
        // keep only letters and capitalize at each split
        return Arrays.stream(str.split("[^A-Za-z]")).map(s -> {
            if (s.isEmpty()) {
                return s;
            }
            if (s.length() >= 3 && s.startsWith("get")) {
                s = s.substring(3);
            }
            if (s.isEmpty()) {
                return s;
            }
            return s.substring(0, 1).toUpperCase()
                    + s.substring(1);
        }).collect(Collectors.joining(""));
    }

    private static String escape(String str) {
        str = str.replace("{", "\\{");
        str = str.replace("}", "\\}");
        str = str.replace("\n", "\\n");
        return str;
    }
}
