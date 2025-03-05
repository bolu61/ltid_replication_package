import traceback
from argparse import ArgumentParser
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from pygit2 import clone_repository

SUBJECTS = [
    ("https://github.com/apache/hadoop", "c835adb3a8d3106493c5b10240593a9693683e5b"),
    ("https://github.com/apache/hive", "4b089c2a48b8d36e5084ce06945722b0ae3f0836"),
    ("https://github.com/apache/hbase", "f8182f582076a633938a0fb79195a38a6cd723f3"),
    ("https://github.com/apache/lucene", "74e3c44063a7e643bcc1c63594d5eb956e050209"),
    ("https://github.com/apache/tomcat", "618a354227e801a95be367496e5fa5cf1a9cf53f"),
    ("https://github.com/apache/activemq", "2ee8700ff3a6778955450f1fbb8dd075bb17f43e"),
    ("https://github.com/apache/pig", "558ccce2ce1a136aa9e94d3a5b7d84187e04865d"),
    ("https://github.com/apache/xmlgraphics-fop", "6ef241f67c4bd27a698c56cdb8edbfade5d8aea4"),
    ("https://github.com/apache/logging-log4j2", "26ace099f3d1ebcce041660fddfea41b0b86f4be"),
    ("https://github.com/apache/ant", "146baefac2d0d1e12fe86ee5215317a4bcb1ff9e"),
    ("https://github.com/apache/struts", "90f984ca85f102ea48ce42944cbe460c74484566"),
    ("https://github.com/apache/jmeter", "3e9af5de35718ae31eabcd2e46cd5462760091ed"),
    ("https://github.com/apache/karaf", "efdf64d27afddcfa04e15916aba11581e5acfab4"),
    ("https://github.com/apache/zookeeper", "3c4e15ef8d1f9969bd69c545f2e88eefeec5cb93"),
    ("https://github.com/apache/mahout", "a414865194d7709044555bbf872d7f09b7763ba8"),
    ("https://github.com/apache/openmeetings", "f2a1fc6d4dda3c878c55c18de127f4ecc67b1009"),
    ("https://github.com/apache/maven", "f137c13877e943bacfb2af3d4072c9155ce48bc5"),
    ("https://github.com/apache/pivot", "6d30e1dfb45b97f26a49833acb3ab8a7198eac5b"),
    ("https://github.com/apache/empire-db", "67a97c9221f5509a478b1a8d77725ad31ea4dc38"),
    ("https://github.com/apache/mina", "cd62e266374ef7a040de7a39c711c87a00cd498c"),
    ("https://github.com/apache/creadur-rat", "84041b3b362eff435528d87dd0783947bb1d5932"),
]  # fmt: skip


def main():
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--path", type=Path, default=Path.cwd())
    args = argument_parser.parse_args()

    cast(Path, args.path).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor() as executor:
        for url, commit in SUBJECTS:
            executor.submit(clone, url, args.path, commit)


def with_exception[**T, S](f: Callable[T, S]):
    def g(*args: T.args, **kwargs: T.kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            traceback.print_exception(e)

    return g


@with_exception
def clone(url: str, path: Path, ref: str):
    name = url.split("/")[-1]
    repo = clone_repository(url=url, path=str(path / name))
    repo.checkout_tree(ref)
    print(repo.path)


if __name__ == "__main__":
    main()
