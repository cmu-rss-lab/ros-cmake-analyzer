from dataclasses import dataclass
from pathlib import Path

from .package_xml.package import PackageDefinition, parse_package_string


@dataclass
class Package:
    name: str
    path: Path

    definition: PackageDefinition | None

    @classmethod
    def get_package_definition(cls, path: Path) -> PackageDefinition:
        """Return the contents of the package.xml file associated with the package.

        This function reads the package.xml on-demand, and then returns a cached copy thereafter.

        Returns
        -------
        PackageDefinition
            The definition of the pacakge as defined in package.xml

        """
        package_xml = path / "package.xml"
        if not package_xml.is_file():
            pacakge_xml = path / "manifest.xml"
            if not pacakge_xml.is_file():
                raise ValueError(f"No package.xml for package {path!s}")

        with package_xml.open() as f:
            contents = f.read()
        return parse_package_string(contents, filename=package_xml)  # type: ignore

    @classmethod
    def from_dir(cls, directory: Path) -> "Package":
        defn = cls.get_package_definition(directory)
        return cls(defn.name, directory, defn)
