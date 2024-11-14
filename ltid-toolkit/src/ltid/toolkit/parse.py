from lxml import etree
from pylibsrcml.srcml import srcml_archive, srcml_unit


class Parser:
    _archive: srcml_archive
    _xmlparser: etree.XMLParser

    def __init__(self, language: str):
        self._archive = srcml_archive()
        self._archive.set_language(language)

        self._xmlparser = etree.XMLParser(
            huge_tree=True,
            ns_clean=True,
            recover=True,
            encoding="utf-8",
        )

    def parsestring(self, code: str):
        unit = srcml_unit(self._archive)
        unit.parse_memory(code)

        srctree = unit.get_srcml()
        return etree.fromstring(srctree, parser=self._xmlparser)
