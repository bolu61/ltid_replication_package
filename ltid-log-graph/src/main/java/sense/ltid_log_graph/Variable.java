package sense.ltid_log_graph;

import spoon.reflect.declaration.CtElement;

public interface Variable {
    String name();

    int id();

    CtElement element();
}
