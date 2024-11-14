/**
 * singly inked list of code fragments
 */
package ltid.log_graph.fragments;

import java.util.Iterator;
import java.util.NoSuchElementException;
import java.util.Objects;

public class Fragment {
    private String code;

    private Fragment nextsource;
    private Fragment nextnormal;

    /**
     * create a new fragment from source code
     */
    Fragment(String code) {
        this(code, null);
    }

    private Fragment(String code, Fragment next) {
        this(code, next, next);
    }

    private Fragment(String code, Fragment nextsource, Fragment nextnormal) {
        this.code = Objects.requireNonNull(code);
        this.nextsource = nextsource;
        this.nextnormal = nextnormal;
    }

    /**
     * 
     * @return the length of the contained fragment of code
     */
    public int length() {
        return code.length();
    }

    /**
     * insert some code at the start of this fragment
     * @param code the code to insert
     * @return
     */
    public Fragment insert(String code) {
        nextnormal = new Fragment(code, split(0));
        return nextnormal;
    }

    public Fragment append(String code) {
        nextnormal = new Fragment(code, next());
        return nextnormal;
    }

    /**
     * delete the code in this fragment
     * @return
     */
    public String delete() {
        var fragment = split(0);
        nextnormal = fragment.next();
        return fragment.toString();
    }

    /**
     * split this fragment into two fragments
     *
     * @param index index at which this fragment is split
     * @return the created fragment
     */
    public Fragment split(int index) {
        nextsource = nextnormal = new Fragment(code.substring(index), nextsource, next());
        code = code.substring(0, index);
        return nextsource;
    }

    /**
     * get the fragment that follows this fragment
     * @return the following fragment
     */
    public Fragment next() {
        return nextnormal;
    }

    @Override
    public String toString() {
        return code;
    }

    public Fragment restore() {
        nextnormal = nextsource;
        return this;
    }

    public Iterable<Fragment> source(Fragment bound) {
        return () -> new Iterator<>() {
            Fragment fragment = new Fragment("", Fragment.this, Fragment.this);

            @Override
            public boolean hasNext() {
                var next = fragment.next();
                return next != null && next != bound;
            }

            @Override
            public Fragment next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }

                fragment = fragment.nextsource;
                return fragment;
            }
        };
    }

    public FragmentList range(Fragment bound) {
        return new FragmentList(this, bound);
    }

    public Iterable<Fragment> through(Fragment bound) {
        return () -> new Iterator<>() {
            Fragment fragment = new Fragment("", Fragment.this, Fragment.this);

            @Override
            public boolean hasNext() {
                var next = fragment.next();
                return next != null && next != bound;
            }

            @Override
            public Fragment next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }

                fragment = fragment.next();
                return fragment;
            }
        };
    }
}