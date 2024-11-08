package sense.logid.fragments;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class FragmentList {
    Fragment head;
    Fragment last;

    public FragmentList(String code) {
        this(new Fragment(code), null);
    }

    FragmentList(Fragment head, Fragment last) {
        this.head = Objects.requireNonNull(head);
        this.last = last;
    }

    public List<FragmentList> split(String separator) {
        var list = new ArrayList<FragmentList>();

        var piece = this;
        while (true) {
            var offset = piece.index(separator);

            if (offset == null) {
                list.add(piece);
                return list;
            }

            list.add(piece.head().range(offset));

            piece = at(offset, separator.length()).range(last);
        }
    }

    public FragmentList copy() {
        return new FragmentList(head, last);
    }

    public Fragment index(String string) {
        for (var piece : head.through(last)) {
            var code = piece.toString();
            var indx = code.indexOf(string);

            if (indx >= 0) {
                return piece.split(indx);
            }

            for (int offset = 0; offset < code.length(); offset++) {
                if (string.startsWith(code.substring(offset))
                        && startswith(piece.next(), string.substring(code.length() - offset))) {
                    return piece.split(offset);
                }
                code = code.substring(1);
            }
        }

        return null;
    }

    public boolean startswith(String string) {
        return startswith(head, string);
    }

    private boolean startswith(Fragment offset, String string) {
        for (var fragment : offset.through(last)) {
            var code = fragment.toString();
            if (code.startsWith(string)) {
                return true;
            }
            if (!string.startsWith(code)) {
                return false;
            }
            string = string.substring(code.length());
        }
        return string.length() == 0;
    }

    public boolean endswith(String string) {
        for (var fragment : head.through(last)) {
            if (string.length() == 0) {
                return false;
            }

            var prefix = fragment.toString();
            while (prefix.length() > 0) {
                if (string.startsWith(prefix)) {
                    string = string.substring(prefix.length());
                    break;
                }
                prefix = prefix.substring(1);
            }
        }
        return string.length() == 0;
    }

    public Fragment head() {
        return head;
    }

    public Fragment last() {
        return last;
    }

    public int length() {
        int length = 0;
        for (var p = head; p != last; p = p.next()) {
            length += p.length();
        }
        return length;
    }

    public boolean empty() {
        return length() == 0;
    }

    public FragmentList insert(Fragment offset, String code) {
        var fragment = offset.insert(code);
        return new FragmentList(fragment, fragment.next());
    }

    public String delete(Fragment offset, int count) {
        var builder = new StringBuilder();
        for (var piece : offset.through(last)) {
            if (count == 0) {
                return builder.toString();
            }
            if (count < piece.length()) {
                piece.split(count);
                builder.append(piece.delete());
                break;
            }
            count -= piece.length();
            builder.append(piece.delete());
        }
        return builder.toString();
    }

    public boolean contains(String string) {
        return index(string) != null;
    }

    public boolean contains(Fragment fragment) {
        return contains(head, fragment);
    }

    private boolean contains(Fragment offset, Fragment fragment) {
        for (var i : offset.through(last)) {
            if (i == fragment) {
                return true;
            }
        }
        return false;
    }

    public Fragment at(int index) {
        return at(head, index);
    }

    private Fragment at(Fragment offset, int index) {
        for (var piece : offset.through(last)) {
            if (index == 0) {
                return piece;
            }
            if (index < piece.length()) {
                return piece.split(index);
            }
            index -= piece.length();
        }

        if (index != 0) {
            throw new IndexOutOfBoundsException();
        }

        return last;
    }

    @Override
    public String toString() {
        var string = new StringBuilder();
        for (var piece : head.through(last)) {
            string.append(piece.toString());
        }
        return string.toString();
    }
}