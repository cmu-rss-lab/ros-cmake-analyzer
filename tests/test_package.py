from pathlib import Path

from ros_cmake_analyzer.core.package import Package


def test_simple_package() -> None:
    package = Package.from_dir(Path("tests/test_packages/car_demo"))
    assert package.name == "car_demo"
    assert len(package.definition.exports) == 1
