package ltid.log_graph;

import java.util.Iterator;
import java.util.NoSuchElementException;

public class Counter implements Iterable<Integer> {
    private int value = 0;
    private boolean overflow = false;

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<Integer>() {

            @Override
            public boolean hasNext() {
                return !overflow;
            }

            @Override
            public Integer next() {
                if (overflow) {
                    throw new NoSuchElementException();
                }
                try {
                    return value++;
                } finally {
                    if (value == 0) {
                        overflow = true;
                    }
                }
            }
        };
    }
}
