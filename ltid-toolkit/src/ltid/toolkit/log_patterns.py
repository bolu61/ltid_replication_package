import re
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime, timedelta
from functools import partial
from itertools import count
from math import floor
from pathlib import Path

import pandas as pd
from numpy.typing import ArrayLike
from prefixspan import make_trie, trie

type Loc = tuple[Path, int]


def make_pattern_tree(
    log_files: list[Path],
    sequence_duration: timedelta,
    min_support_ratio: float,
) -> trie:
    id_counter = count()
    loc_to_id_map: dict[Loc, int] = defaultdict(lambda: next(id_counter))

    def get_event_id(log: str) -> tuple[datetime, int]:
        """get (timestamp, event_id)"""
        if m := re.match(r"TODO", log):
            return (
                datetime.fromisoformat(m.group("timestamp")),
                loc_to_id_map[(Path(m.group("file")), int(m.group("line")))],
            )
        raise ValueError(f"failed to parse {log=}")

    @partial(lambda x: list(x()))
    def dataset() -> Iterator[ArrayLike]:
        for log_file in log_files:
            with log_file.open("r") as fp:
                timestamp, event_ids = zip(*(get_event_id(log) for log in fp))
            series = pd.Series(event_ids, index=timestamp)
            yield from series.rolling(sequence_duration)

    minsup = floor(min_support_ratio * len(dataset))

    return make_trie(dataset, minsup)
