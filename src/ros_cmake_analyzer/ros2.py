import typing as t
from loguru import logger
from pathlib import Path

from ros_cmake_analyzer import CMakeExtractor
from ros_cmake_analyzer.decorator import (
    aliased_cmake_command,
    cmake_command,
)
from ros_cmake_analyzer.model import (
    CMakeBinaryTarget, CMakeInfo,
    DUMMY_VALUE, IncompleteCMakeLibraryTarget, SourceLanguage,
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

        info = self._info_from_cmakelists()
        self._hook_libraries_into_executables(info)
        return info

    def _get_global_cmake_variables(self) -> dict[str, str]:
        dict_: dict[str, t.Any] = {
            "CMAKE_SOURCE_DIR": "",
            "PROJECT_SOURCE_DIR": "",
            "CMAKE_CURRENT_SOURCE_DIR": "",
            "PROJECT_VERSION": DUMMY_VALUE,
        }
        return dict_

    @aliased_cmake_command("ament_python_install_package")
    def python_install_package(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        # https://docs.ros.org/en/foxy/How-To-Guides/Ament-CMake-Python-Documentation.html
        # This installs a directory as a module that can be used in python as a library
        opts, args = self._cmake_argparse(raw_args, {})
        name = args[0]
        # Check that directory has __init__.py, otherwise it isn't valid
        # sources should be all python files in the module?
        directory = Path(name)
        if "cwd" in cmake_env:
            directory = Path(cmake_env["cwd"]) / directory
        directory = self.package.path / directory
        if not directory.is_dir():
            raise FileNotFoundError(f"Directory {directory!s} does not exist")
        if not (directory / "__init__.py").is_file():
            raise FileNotFoundError(f"Directory {directory!s} does not contain __init__.py")
        sources = [file for file in directory.glob("*.py") if file.name != "__init__.py"]
        self.executables[name] = IncompleteCMakeLibraryTarget(
            name,
            SourceLanguage.PYTHON,
            set(sources),
            [],
            self.package_paths(),
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=cmake_env["cmakelists_line"],
        )

    @cmake_command
    def rclcpp_components_register_node(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {
            "PLUGIN": "*",
            "EXECUTABLE" : "*",
            "RESOURCE_INDEX": "*",
        })
        if "PLUGIN" not in opts or "EXECUTABLE" not in opts:
            logger.error("Need PLUGIN and EXECUTABLE arguments")
            raise ValueError("Need PLUGIN and EXECUTABLE arguments")
        self.executables[opts.get("EXECUTABLE")[0]] = CMakeBinaryTarget(
            name=opts.get("EXECUTABLE")[0],
            language=SourceLanguage.CXX,
            sources=set(opts.get("PLUGIN")),
            includes=cmake_env["INCLUDE_DIRECTORIES"].split(" ") if "INCLUDE_DIRECTORIES" in cmake_env else [],
            libraries=[],
            restrict_to_paths=self.package_paths(),
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=cmake_env["cmakelists_line"],
        )

    @cmake_command
    def rclcpp_components_register_nodes(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {"RESOURCE_INDEX": "*"})
        self.executables[args[0]] = CMakeBinaryTarget(
            name=args[0],
            language=SourceLanguage.CXX,
            sources=set(args[1:]),
            includes=cmake_env["INCLUDE_DIRECTORIES"].split(" ") if "INCLUDE_DIRECTORIES" in cmake_env else [],
            libraries=[],
            restrict_to_paths=self.package_paths(),
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=cmake_env["cmakelists_line"],
        )
