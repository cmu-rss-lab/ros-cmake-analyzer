from __future__ import annotations

__all__ = ("Package",)

import defusedxml
from dataclasses import dataclass
from pathlib import Path

from defusedxml.ElementTree import ParseError as XmlParseError
from defusedxml.ElementTree import parse as parse_xml
import defusedxml.ElementTree

from .package_xml.package import Export


@dataclass
class Package:
    name: str
    path: Path
    filename: str
    format_version: str | None
    exports: list[Export]

    @classmethod
    def get_package_definition(cls, path: Path) -> Package:
        """Return the contents of the package.xml file associated with the package.

        This function reads the package.xml on-demand, and then returns a cached copy thereafter.

        Returns
        -------
        PackageDefinition
            The definition of the pacakge as defined in package.xml

        """
        package_xml_path = path / "package.xml"
        if not package_xml_path.is_file():
            package_xml_path = path / "manifest.xml"
            if not package_xml_path.is_file():
                raise ValueError(f"No package.xml for package: {path!s}")

        package_xml = parse_xml(package_xml_path)
        root = package_xml.getroot()
        if root.tag != "package":
            raise ValueError(f"Invalid package.xml: {package_xml_path!s}")
        format_version = root.attrib.get("format")
        plugin_description_exports: list[Export] = []

        for child in root:
            if child.tag == "export":
                export = Export(str(child.tag), _get_node_value(child, allow_xml=True))
                for key, value in child.attrib.items():
                    export.attributes[str(key)] = str(value)
                plugin_description_exports.append(export)

        return Package(
            name=package_xml_path.parent.name,
            path=package_xml_path.parent,
            filename=package_xml_path.stem,
            format_version=format_version,
            exports=plugin_description_exports,
        )

    @classmethod
    def from_dir(cls, directory: Path) -> Package:
        return cls.get_package_definition(directory)


def _get_node_value(node: defusedxml.ElementTree, allow_xml: bool=False, apply_str: bool=True):
    if allow_xml:
        value = ("".join(defusedxml.ElementTree.tostring(n).decode() for n in node)).strip(" \n\r\t")
    else:
        value = ("".join([n.data for n in node if n.nodeType == n.TEXT_NODE])).strip(" \n\r\t")
    if apply_str:
        value = str(value)
    return value