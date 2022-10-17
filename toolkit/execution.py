from concurrent.futures import ThreadPoolExecutor
from collections import deque
from contextlib import contextmanager
import sys

from tqdm import tqdm
from tqdm.contrib import DummyTqdmFile


@contextmanager
def redirect():
    if isinstance(sys.stdout, DummyTqdmFile) and isinstance(sys.stdout, DummyTqdmFile):
        yield redirect.stdout, redirect.stderr
        return

    redirect.stdout = sys.stdout
    redirect.stderr = sys.stderr
    sys.stdout = DummyTqdmFile(sys.stdout)
    sys.stderr = DummyTqdmFile(sys.stderr)
    try:
        yield redirect.stdout, redirect.stderr
    finally:
        sys.stdout = redirect.stdout
        sys.stderr = redirect.stderr


def bar(iterable, total=None, desc=None):
    with redirect() as fds:
        yield from tqdm(iterable, total=total, file=fds[1], leave=False, desc=desc)


def consume(iterable):
    deque(iterable, maxlen=0)


def do(task, *args):
    with ThreadPoolExecutor() as executor:
        yield from executor.map(task, *args)
