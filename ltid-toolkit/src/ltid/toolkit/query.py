import re
from importlib import resources

from lxml import etree

ns = {"src": "http://www.srcML.org/srcML/src"}

query_variables = etree.XPath("//src:name/text()", namespaces=ns)

is_logging_statement = etree.RelaxNG(
    etree.parse(str(resources.files() / "logpattern.rng"), parser=None)
)


def extract_log(root):
    """find first logging statement"""
    for call in root.iter(r"{*}call"):
        if is_logging_statement(call):
            yield call


_WORD = re.compile(r"[a-zA-Z][a-z]*")

ID_HEURISTICS = [
    "id",
    "path",
    "address",
    "host",
    "ip",
    "name",
    "url",
    "uri",
]


def is_id(variable: str):
    for word in _WORD.findall(variable):
        for heuristic in ID_HEURISTICS:
            if word.lower().endswith(heuristic):
                return True
    return False


def extract_id(log):
    for var in query_variables(log):
        if is_id(var):
            yield var
