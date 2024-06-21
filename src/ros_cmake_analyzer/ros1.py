from pathlib import Path

from core.package import Package
from extractor import DUMMY_VALUE, CMakeExtractor, CMakeInfo


class ROS1CMakeExtractor(CMakeExtractor):

    def get_cmake_info(
            self,
            package: Package,
    ) -> CMakeInfo:
        cmakelists_path = package.path / "CMakeLists.txt"
        if not cmakelists_path.is_file():
            msg = f"No `CMakeLists.txt' in {package.name}"
            raise ValueError(msg)

        return self._info_from_cmakelists(package)

    def package_paths(self, package: Package) -> set[Path]:
        paths = {package.path}
        workspace = self._find_package_workspace(package)
        for contender in ("devel/include", "devel_isolated/include", "install/include"):
            workspace_contender = workspace / contender / package.name
            if workspace_contender.exists():
                paths.add(workspace_contender)
        return paths


    def _get_global_cmake_variables(self, package: Package) -> dict[str, str]:
        dict_ = {
            "CMAKE_SOURCE_DIR": "",
            "PROJECT_SOURCE_DIR": "",
            "CMAKE_CURRENT_SOURCE_DIR": "",
            "PROJECT_VERSION": DUMMY_VALUE,
            "CATKIN_GLOBAL_INCLUDE_DESTINATION": "/include",
            "PYTHON_EXT_SUFFIX": '""',
        }
        workspace = self._find_package_workspace(package)
        paths = set()
        for contender in ("devel", "devel_isolated", "install"):
            workspace_contender = workspace / contender
            if workspace_contender.exists():
                paths.add(workspace_contender)
        assert len(paths) == 1
        dict_["CATKIN_DEVEL_PREFIX"] = paths.pop() / package.name
        dict_["CMAKE_BINARY_DIR"] = workspace / "build"
        dict_["CMAKE_CURRENT_BINARY_DIR"] = dict_["CMAKE_BINARY_DIR"] / package.name
        dict_["PROJECT_NAME"] = package.name  # Put package name as default project, overwritten by project(...)
        return dict_

    def _find_package_workspace(self, package: Package) -> Path:
        """Determine the absolute path of the workspace to which a given package belongs.

        Raises
        ------
        ValueError
            if the workspace for the given package could not be determined

        """
        workspace_path = Path(package.path)
        while workspace_path != Path("/"):
            catkin_marker_path = workspace_path / ".catkin_workspace"
            if catkin_marker_path.exists():
                return workspace_path

            catkin_tools_dir = workspace_path / ".catkin_tools"
            if catkin_tools_dir.exists():
                return workspace_path
            workspace_path = workspace_path.parent
        return workspace_path
