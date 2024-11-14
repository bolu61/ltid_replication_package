from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from pygit2 import clone_repository
from pygit2.callbacks import RemoteCallbacks
from pygit2.remotes import TransferProgress
from pygit2.repository import Repository
from tqdm import tqdm


def split_project(path: Path, maxdepth=0):
    if not path.is_dir():
        return

    if maxdepth == 0:
        yield path
        return

    for subpath in path.iterdir():
        if subpath.is_dir():
            yield from split_project(subpath, maxdepth=maxdepth - 1)
        else:
            yield subpath


def project(url: str, path: Path) -> "Project":
    parsed = urlparse(url)
    name = parsed.path.strip("/")
    path = path / name
    path = path.resolve()

    if path.is_dir():
        return Project(name, path, Repository(str(path)))

    with tqdm(desc=f"cloning {parsed.geturl()}", leave=False) as pbar:
        if repo := clone_repository(
            parsed.geturl(), path, callbacks=_RemoteCloneTQDMCallback(pbar)
        ):
            return Project(name, path, repo)
        else:
            raise RepositoryCloneError(
                {
                    "message": "failed to clone repository",
                    "url": url,
                    "path": path,
                }
            )


@dataclass
class Project:
    name: str
    path: Path
    repo: Repository


class RepositoryCloneError(Exception):
    pass


class _RemoteCloneTQDMCallback(RemoteCallbacks):
    pbar: tqdm

    def __init__(self, pbar: tqdm):
        self.pbar = pbar
        self.total = 0
        self.current = 0

    def transfer_progress(self, stats: TransferProgress):
        if self.total != stats.total_objects:
            self.pbar.total = stats.total_objects
            self.total = self.pbar.total
            self.pbar.refresh()
        self.pbar.update(stats.indexed_objects - self.current)
        self.current = stats.indexed_objects
