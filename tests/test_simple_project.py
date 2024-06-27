from pathlib import Path

from ros_cmake_analyzer.core.package import Package
from ros_cmake_analyzer.ros1 import ROS1CMakeExtractor


def test_ros1_car_demo() -> None:
    cmake = ROS1CMakeExtractor("test_packages/car_demo")
    info = cmake.get_cmake_info()
    assert len(info.targets) == 3

def test_ros1_autorally_nodelets() -> None:
    cmake = ROS1CMakeExtractor("test_packages/autorally_core")
    info = cmake.get_cmake_info()
    assert True

