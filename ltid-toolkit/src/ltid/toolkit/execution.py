import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import IO, cast

from tqdm import tqdm
from tqdm.contrib import DummyTqdmFile


@contextmanager
def redirect():
    with redirect_stdout(
        cast(IO[str], DummyTqdmFile(sys.stdout))
    ) as out, redirect_stderr(cast(IO[str], DummyTqdmFile(sys.stderr))) as err:
        yield out, err


def bar(iterable, total=None, desc=None):
    file = sys.stderr
    with redirect():
        yield from tqdm(iterable, total=total, file=file, leave=False, desc=desc)


def consume(iterable):
    deque(iterable, maxlen=0)


def do(task, *args):
    with ThreadPoolExecutor() as executor:
        yield from executor.map(task, *args)
