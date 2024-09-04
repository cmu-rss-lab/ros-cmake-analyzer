import typing as t
from pathlib import Path

from ros_cmake_analyzer import CMakeExtractor
from ros_cmake_analyzer.decorator import (
    aliased_cmake_command,
    cmake_command,
)
from ros_cmake_analyzer.model import (
    CMakeInfo,
    DUMMY_VALUE,
)


class ROS2CMakeExtractor(CMakeExtractor):

    def __init__(self, package_dir: str | Path) -> None:
        super().__init__(package_dir)

    def package_paths(self) -> set[Path]:
        return {self.package.path}

    def get_cmake_info(self) -> CMakeInfo:
        cmakelists_path = self.package.path / "CMakeLists.txt"
        if not cmakelists_path.is_file():
            msg = f"No `CMakeLists.txt' in {self.package.name}"
            raise ValueError(msg)

        return self._info_from_cmakelists()

    def _get_global_cmake_variables(self) -> dict[str, str]:
        dict_: dict[str, t.Any] = {
            "CMAKE_SOURCE_DIR": "",
            "PROJECT_SOURCE_DIR": "",
            "CMAKE_CURRENT_SOURCE_DIR": "",
            "PROJECT_VERSION": DUMMY_VALUE,
        }
        return dict_

    @aliased_cmake_command("ament_python_install_package")
    def python_install_package(self, raw_args: list[str], cmake_env: dict[str, t.Any]) -> None:
        pass

    @cmake_command
    def pluginlib_export_plugin_description_file(self, raw_args: list[str], cmake_env: dict[str, t.Any]) -> None:
        # https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Pluginlib.html
        pass
