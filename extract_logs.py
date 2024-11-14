# !/usr/bin/env python3
import csv
from functools import partial
from itertools import chain
import logging
from pathlib import Path
from typing import List

from package import scratch, subjects
from ltid.toolkit.log_graph import LTIDLogGraphExecutionError, gather
from ltid.toolkit.execution import bar, do
from ltid.toolkit.project import Project, split_project
from ltid.toolkit.query import isid

logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(levelname)s %(message)s')

def process(subjects: List[Project]):
    def process_subject(subject: Project):
        def process_split(split: Path):
            logging.debug('starting %s', split)
            try:
                logtypes = list(gather(split, launcher="file"))
                logging.info("%s", split)
                return logtypes
            except LTIDLogGraphExecutionError:
                logging.warning("failed to extract logs from %s retrying by split", split)
                splits = list(filter(lambda s: s.is_dir() or s.suffix == '.java' and s.stem != 'package-info', split_project(split, maxdepth=4)))
                if len(splits) == 0:
                    logging.exception("can no longer split %s", split)
                logtypes = list(chain.from_iterable(
                    map(partial(process_split), splits)
                ))
                return logtypes

        count = 0
        count_w_id = 0
        count_w_injection = 0
        for logtype in process_split(subject.path):
            count += 1
            if any(isid(variable) for variable in logtype.variables):
                count_w_id += 1
            for dominator in logtype.dominators:
                if any(isid(variable) for variable in dominator.variables):
                    count_w_injection += 1
        return count, count_w_id, count - count_w_id, count_w_injection

    for subject, row in zip(subjects, bar(do(process_subject, subjects), total=len(subjects))):
        yield subject.name, *row


def main():
    with open(scratch() / 'extract_logs.csv', 'w') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        for row in process(subjects()):
            writer.writerow(row)


if __name__ == "__main__":
    main()
