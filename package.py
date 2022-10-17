from pathlib import Path
from typing import List, Optional
from toolkit.project import Project, project
from functools import partial
from toolkit.execution import do


def scratch(name: Optional[str] = None) -> Path:
    """make and get the path to a predefined scratch directory"""
    path = Path(__file__).parent.resolve() / "scratch"
    if name is not None:
        path = path / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def subjects() -> List[Project]:
    """yields repositories subject in the study"""

    get_or_clone = partial(project, path=scratch("subjects"))

    return list(
        do(
            get_or_clone,
            [
                "https://github.com/apache/hadoop",
                "https://github.com/apache/hive",
                "https://github.com/apache/hbase",
                "https://github.com/apache/lucene",
                "https://github.com/apache/tomcat",
                "https://github.com/apache/activemq",
                "https://github.com/apache/pig",
                "https://github.com/apache/xmlgraphics-fop",
                "https://github.com/apache/logging-log4j2",
                "https://github.com/apache/ant",
                "https://github.com/apache/struts",
                "https://github.com/apache/jmeter",
                "https://github.com/apache/karaf",
                "https://github.com/apache/zookeeper",
                "https://github.com/apache/mahout",
                "https://github.com/apache/openmeetings",
                "https://github.com/apache/maven",
                "https://github.com/apache/pivot",
                "https://github.com/apache/empire-db",
                "https://github.com/apache/mina",
                "https://github.com/apache/creadur-rat",
            ],
        )
    )


class RepositoryCloneError(Exception):
    pass
