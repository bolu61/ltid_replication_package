package ltid.log_graph.fragments;

import spoon.reflect.declaration.CtElement;

public class ElementLocator {
    private final CtElement root;
    private final Fragment head;
    private final String source;

    public ElementLocator(CtElement element) {
        this.root = element;
        this.source = element.getPosition().getCompilationUnit().getOriginalSourceCode();
        this.head = new Fragment(source);
    }

    public String source() {
        return source;
    }

    public FragmentList locate() {
        return new FragmentList(head, null);
    }

    public FragmentList locate(CtElement element) {
        if (!element.hasParent(root) && !element.equals(root)) {
            throw new MissedSnipeException(element);
        }

        var pos = element.getPosition();
        var start = pos.getSourceStart();
        var end = pos.getSourceEnd() + 1;
        
        var offset = locate(start);
        return offset.range(offset.range(null).at(end - start));
    }

    private Fragment locate(int index) {
        for (var piece : head.source(null)) {
            if (index == 0) {
                return piece;
            }
            if (index < piece.length()) {
                return piece.split(index);
            }

            index -= piece.length();
        }

        throw new IndexOutOfBoundsException();
    }

    public class MissedSnipeException extends RuntimeException {
        private final CtElement element;

        public MissedSnipeException(CtElement element) {
            super(String.format("%s is not a decendant of %s", element, root));
            this.element = element;
        }

        public CtElement target() {
            return element;
        }

        public ElementLocator locate() {
            return ElementLocator.this;
        }
    }
}
