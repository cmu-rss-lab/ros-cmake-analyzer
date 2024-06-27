from pathlib import Path

from ros_cmake_analyzer.core.package import Package
from ros_cmake_analyzer.ros1 import ROS1CMakeExtractor


def test_ros1_car_demo() -> None:
    cmake = ROS1CMakeExtractor()
    package = Package.from_dir(Path("test_packages/car_demo"))
    info = cmake.get_cmake_info(package)
    assert len(info.targets) == 3
