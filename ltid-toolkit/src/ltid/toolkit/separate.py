from functools import partial
import sys
from collections.abc import Callable, Generator, Iterable

import numpy as np

from typing import Iterator, Protocol


class Trie[K](Protocol):
    def __getitem__(self, key: K, /) -> "Trie[K]": ...

    def __contains__(self, key: K, /) -> bool: ...

    def __iter__(self) -> Iterator[tuple[K, "Trie[K]"]]: ...

    @property
    def keys(self) -> Iterator[K]: ...

    @property
    def count(self) -> int: ...


def match[K](trie: Trie[K], seq: list[K]) -> Generator[int, None, None]:
    i = -1
    j = 0
    while i < j and j < len(seq):
        if seq[j] not in trie:
            return
        trie = trie[seq[j]]
        yield j
        i = j

        for k in sorted(trie.keys, key=lambda k: trie[k].count, reverse=True):
            try:
                j = seq.index(k, i + 1)
                break
            except ValueError:
                continue


def extract[T](idx: list[int], seq: list[T]) -> list[T]:
    extracted = [seq.pop(i) for i in reversed(idx)]
    extracted.reverse()
    return extracted


def separate[T, K](
    trie: Trie[K], seq: Iterable[T], key: Callable[[T], K] = lambda x: x
) -> Generator[list[T], None, None]:
    seq_list = [*seq]
    while len(seq_list) > 0:
        keys = [key(s) for s in seq_list]
        extracted = extract([*match(trie, keys)], seq_list)
        if len(extracted) > 0:
            yield extracted
        else:
            yield [seq_list.pop(0)]


if __name__ == "__main__":
    from prefixspan import make_trie

    sequences = [[1, 2, 3], [2, 2, 3], [2, 3, 1], [3, 2, 1], [2, 1, 1]]
    db = [*map(partial(np.array, dtype=np.uint64), sequences)]

    trie: Trie[int] = make_trie(db, minsup=3)
    sys.stdout.write(f"{trie}\n")

    for seq in separate(trie, [4, 2, 2, 3, 1], lambda x: x):
        sys.stdout.write(f"{seq}\n")
