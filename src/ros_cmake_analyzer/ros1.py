# ruff: noqa: ERA001
import typing as t
from pathlib import Path

from .core.package import Package
from .extractor import CMakeExtractor, CMakeInfo, DUMMY_VALUE


class ROS1CMakeExtractor(CMakeExtractor):

    def __init__(self, package_dir: str | Path) -> None:
        super().__init__(package_dir)

    def get_cmake_info(self) -> CMakeInfo:
        cmakelists_path = self.package.path / "CMakeLists.txt"
        if not cmakelists_path.is_file():
            msg = f"No `CMakeLists.txt' in {self.package.name}"
            raise ValueError(msg)

        return self._info_from_cmakelists()

    def package_paths(self) -> set[Path]:
        paths: set[Path] = {self.package.path}
        # This code requires catkin builds, so not included here
        # workspace = self._find_package_workspace(package)
        # for contender in ("devel/include", "devel_isolated/include", "install/include"):
        #     workspace_contender = workspace / contender / package.name
        #     if workspace_contender.exists():
        #         paths.add(workspace_contender)
        return paths

    def _get_global_cmake_variables(self) -> dict[str, t.Any]:
        dict_: dict[str, t.Any] = {
            "CMAKE_SOURCE_DIR": "",
            "PROJECT_SOURCE_DIR": "",
            "CMAKE_CURRENT_SOURCE_DIR": "",
            "PROJECT_VERSION": DUMMY_VALUE,
            "CATKIN_GLOBAL_INCLUDE_DESTINATION": "/include",
            "PYTHON_EXT_SUFFIX": '""',
        }
        workspace = self._find_package_workspace()
        paths = set()
        for contender in ("devel", "devel_isolated", "install"):
            workspace_contender = workspace / contender
            if workspace_contender.exists():
                paths.add(workspace_contender)
        assert len(paths) == 1
        dict_["CATKIN_DEVEL_PREFIX"] = paths.pop() / self.package.name
        dict_["CMAKE_BINARY_DIR"] = workspace / "build"
        dict_["CMAKE_CURRENT_BINARY_DIR"] = dict_["CMAKE_BINARY_DIR"] / self.package.name
        dict_["PROJECT_NAME"] = self.package.name  # Put package name as default project, overwritten by project(...)
        return dict_

    def _find_package_workspace(self) -> Path:
        """Determine the absolute path of the workspace to which a given package belongs.

        Raises
        ------
        ValueError
            if the workspace for the given package could not be determined

        """
        workspace_path = self.package.path
        while workspace_path != Path("/"):
            catkin_marker_path = workspace_path / ".catkin_workspace"
            if catkin_marker_path.exists():
                return workspace_path

            catkin_tools_dir = workspace_path / ".catkin_tools"
            if catkin_tools_dir.exists():
                return workspace_path
            workspace_path = workspace_path.parent
        return workspace_path
