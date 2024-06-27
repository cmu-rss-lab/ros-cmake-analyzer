from dataclasses import dataclass

from defusedxml import ElementTree as ET  # noqa: N817
from loguru import logger


@dataclass
class NodeletLibrary:
    """Represents a piece of information found in the nodelet_plygin.xml file.

    path: str
        The path to the library containing the nodelet
    nodelet_name: str
        The class name of the main entrypoint for the nodelet
    class_name: str
        The type of the class
    """

    path: str
    name: str
    type_: str

    @property
    def entrypoint(self) -> str:
        return self.type_ + "::onInit"


@dataclass
class NodeletsInfo:
    libraries: list["NodeletLibrary"]

    @classmethod
    def from_nodelet_xml(cls, contents: str) -> "NodeletsInfo":
        libraries: list["NodeletLibrary"] = []
        contents = "<root>\n" + contents + "\n</root>"
        tree = ET.fromstring(contents)
        root = get_xml_nodes_by_name("root", tree)[0]
        libraries_dom = get_xml_nodes_by_name("library", root)
        if not libraries_dom:
            logger.warning("Expected there to be <library/> elements in nodelet_plugins.xml, but there are none.")
            logger.debug(contents)
        for library_dom in libraries_dom:
            path = library_dom.getAttribute("path")
            class_doms = get_xml_nodes_by_name(
                "class",
                library_dom,
            )
            for class_dom in class_doms:
                name = class_dom.getAttribute("name")
                type_ = class_dom.getAttribute("type")
                libraries.append(NodeletLibrary(path=path,
                                                name=name,
                                                type_=type_,
                                                ))
        return NodeletsInfo(libraries=libraries)


def get_xml_nodes_by_name(tag_name: str, tree: ET) -> list[ET]:
    return [n for n in tree.childNodes
            if n.nodeType == n.ELEMENT_NODE and n.tagName == tag_name]
