package anana2.sense.logid;

import spoon.reflect.declaration.CtElement;

public interface Variable {
    String name();

    int id();

    CtElement element();
}
