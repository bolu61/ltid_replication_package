# !/usr/bin/env python3
import csv
import logging
import sys
from pathlib import Path
from typing import List

from ltid.toolkit.log_graph import LogGraph
from ltid.toolkit.project import Project
from ltid.toolkit.query import isid

from package import subjects


def process_split(split: Path):
    logging.debug("starting %s", split)
    log_graph = LogGraph.from_source(split, launcher="maven")
    logging.info("%s", split)
    return log_graph


def process_subject(subject: Project):
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


def process(subjects: List[Project]):
    for subject in subjects:
        row = process_subject(subject)
        yield subject.name, *row


def main():
    writer = csv.writer(sys.stdout, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
    for row in process(subjects()):
        writer.writerow(row)


if __name__ == "__main__":
    main()
