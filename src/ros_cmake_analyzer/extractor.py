from __future__ import annotations

import abc
from charset_normalizer import from_path
import re
import typing as t
from pathlib import Path

from loguru import logger

from .cmake_parser.parser import ParserContext
from .cmake_parser.parser import argparse as cmake_argparse
from .core.nodelets_xml import NodeletsInfo, NodeletLibrary
from .core.package import Package
from .decorator import aliased_cmake_command, TCMakeFunction, CommandHandlerType, cmake_command
from .model import (
    CMakeBinaryTarget,
    CMakeInfo,
    CMakeLibraryTarget, CMakePluginReference, CMakeTarget, CommandInformation,
    FileInformation,
    IncompleteCMakeLibraryTarget,
    SourceLanguage,
)
from .utils import key_val_list_to_dict

__all__ = ("CMakeExtractor",)


class CMakeExtractor(metaclass=CommandHandlerType):
    _files_generated_by_cmake: t.ClassVar[set[str]] = set()
    _files_not_resolved: t.ClassVar[list[FileInformation]] = []
    _commands_not_process: t.ClassVar[list[CommandInformation]] = []

    def __init__(self, package_dir: str | Path) -> None:
        package_path = Path(package_dir) if isinstance(package_dir, str) else package_dir
        self.package = Package.from_dir(package_path)

    def command_for(self, command: str) -> TCMakeFunction | None:
        for h in type(self).__mro__:
            if hasattr(h, "_handlers") and command in h._handlers:
                return h._handlers[command]
        return None

    @abc.abstractmethod
    def package_paths(self) -> set[Path]:
        ...

    @abc.abstractmethod
    def get_cmake_info(self) -> CMakeInfo:
        ...

    @abc.abstractmethod
    def _get_global_cmake_variables(self) -> dict[str, str]:
        ...

    def _hook_libraries_into_executables(self, info: CMakeInfo) -> None:
        for name, target in info.targets.items():
            if name in self.libraries_for:
                target.libraries.extend(self.libraries_for[name] if self.libraries_for[name] is not None else [])

    def get_nodelet_entrypoints(self) -> t.Mapping[str, NodeletLibrary]:
        """Returns the potential nodelet entrypoints and classname for the package.

        Parameters
        ----------
        package: Package
            The package to get nodelet info from

        Returns
        -------
        Mapping[str, NodeletLibrary]
            A mapping of nodelet names to NodeletInfo

        """
        nodelets_xml_path = self.package.path / "nodelet_plugins.xml"
        if not nodelets_xml_path.exists():
            # Read from package
            for export in self.package.exports:
                logger.debug("Looking for export in package.xml")
                if export.tagname == "nodelet" and "plugin" in export.attributes:
                    plugin = export.attributes["plugin"]
                    plugin = plugin.replace("${prefix}", "")
                    nodelets_xml_path = self.package.path / plugin
                    if nodelets_xml_path.exists():
                        logger.debug(f"Reading plugin information from {nodelets_xml_path!s}")
                        break
        if nodelets_xml_path.exists():
            logger.debug(f"Reading plugin information from {nodelets_xml_path}")
            with nodelets_xml_path.open("r") as f:
                contents = f.read()
            logger.debug(f"Contents of that file: {contents}")
            nodelet_info = NodeletsInfo.from_nodelet_xml(contents)
            # If the name is of the form package/nodelet then just return it keyed by nodelete
            # otherwise key by the full name
            entrypoints = {info.name.split("/")[1]: info for info in nodelet_info.libraries if "/" in info.name}
            entrypoints.update({info.name: info for info in nodelet_info.libraries if "/" not in info.name})
            return entrypoints
        return {}

    def _info_from_cmakelists(self) -> CMakeInfo:
        path = self.package.path / "CMakeLists.txt"
        # with path.open(encoding="utf_8") as f:
        #     contents = "".join(f.readlines())
        contents = str(from_path(path).best())
        env: dict[str, str] = {"cmakelists": str(path)}
        return self._process_cmake_contents(contents, env)

    def _cmake_argparse(self, args, opts):   # noqa: ANN202, ANN001
        return cmake_argparse(args, opts)

    def _process_cmake_contents(
            self,
            file_contents: str,
            cmake_env: dict[str, str],
    ) -> CMakeInfo:
        """Processes the contents of a CMakeLists.txt file.

        Adds information about executables. Recursively includes
        other CMakeLists.txt files that may be included.

        Parameters
        ----------
        file_contents: str
            The contents of the CMakeLists.txt file
        package: Package
            The package where the CMakeLists.txt file is defined
        cmake_env: t.Dict[str, str]
            Any context variables for processing the contents

        Returns
        -------
        CMakeInfo:
            Information about the targets in CMakeLists.txt

        """
        pc = ParserContext()
        context = pc.parse(file_contents, skip_callable=False, var=cmake_env)
        self.executables: dict[str, CMakeTarget] = {}
        self.libraries: dict[str, CMakeTarget] = {}
        self.libraries_for: dict[str, list[str]] = {}
        self.plugin_references: list[CMakePluginReference] = []
        for cmd, raw_args, _arg_tokens, (_fname, line, _column) in context:
            cmake_env["cmakelists_line"] = line
            try:
                cmd = cmd.lower()    # noqa: PLW2901
                command = self.command_for(cmd)
                if command:
                    command(self, cmake_env, raw_args)
                else:
                    self._commands_not_process.append(CommandInformation([cmd, raw_args],
                                                                         Path(cmake_env["cmakelists"]),
                                                                         line))
            except BaseException:  # noqa:BLE001  Don't want to crash, just want to report
                logger.error(f"Error processing {cmd}({raw_args}) in "
                             f"{cmake_env['cmakelists'] if 'cmakelists' in cmake_env else 'unknown'}:{line}")
                self._commands_not_process.append(CommandInformation([cmd, raw_args],
                                                                     Path(cmake_env["cmakelists"]),
                                                                     line))
                # raise
        return CMakeInfo(Path(cmake_env["cmakelists"]), self.executables,
                         plugin_references=tuple(self.plugin_references),
                         generated_sources=self._files_generated_by_cmake,
                         unprocessed_commands=self._commands_not_process,
                         unresolved_files=self._files_not_resolved)

    @cmake_command
    def project(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {})
        cmake_env["PROJECT_NAME"] = args[0]
        logger.info(f"Setting PROJECT_NAME={args[0]}")

    @cmake_command
    def set_target_properties(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {"PROPERTIES": "*"})
        properties = key_val_list_to_dict(opts.get("PROPERTIES", []))
        if "OUTPUT_NAME" in properties:
            var_pattern = re.compile(r"([^$]*)\${([^}]*)}(.*)")
            var_match = var_pattern.match(args[0])
            if var_match:
                args[0] = var_match.group(1) + cmake_env[var_match.group(2)] + var_match.group(3)
            if args[0] in self.executables:
                object.__setattr__(self.executables[args[0]], "name", properties["OUTPUT_NAME"])
                logger.info(f"Changed the name of the executable to {properties["OUTPUT_NAME"]}")
                # self.executables[args[0]].name = properties["OUTPUT_NAME"]
                # self.executables[properties["OUTPUT_NAME"]] = self.executables[args[0]]
                # del self.executables[args[0]]
            else:
                logger.error(f"{args[0]} is not in the list of targets")

    @cmake_command
    def set(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"PARENT_SCOPE": "-", "FORCE": "-", "CACHE": "*"},
        )
        cmake_env[args[0]] = ";".join(args[1:])

    @cmake_command
    def unset(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {"CACHE": "-"})
        cmake_env[args[0]] = ""

    @cmake_command
    def aux_source_directory(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        # aux_source_directory(<dir> <var>)
        # Collects the names of all the source files in the specified directory and
        # stores the list in the <variable>
        # https://cmake.org/cmake/help/latest/command/aux_source_directory.html
        var_name = raw_args[1]
        dir_name = Path(raw_args[0])
        path = self.package.path / cmake_env["cwd"] / dir_name if "cwd" in cmake_env else self.package.path / dir_name
        values = ";".join(str(dir_name / f) for f in path.glob("*"))
        cmake_env[var_name] = values

    @aliased_cmake_command("list")
    def list_directive(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        logger.info(f"Processing list directive: {raw_args}")
        opts, args = self._cmake_argparse(raw_args, {"APPEND": "-"})
        if not opts["APPEND"]:
            logger.warning(f"Cannot process list({args[0]} ...)")
            return
        append_to = cmake_env.setdefault(args[0], [])
        if isinstance(append_to, str):
            if append_to:
                append_to += f";{args[1]}"
            else:
                append_to = args[1]
            cmake_env[args[0]] = append_to
        elif isinstance(append_to, list) and len(args) > 1:
            append_to.append(args[1])
        else:
            logger.error(f"Don't know how to append_to append append_to type: {type(append_to)}")

    @cmake_command
    def file(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        logger.debug(f"Processing file directive: {raw_args}")
        opts, args = self._cmake_argparse(raw_args, {"FOLLOW_SYMLINKS": "-",
                                               "LIST_DIRECTORIES": "?",
                                               "RELATIVE": "?",
                                               "GLOB_RECURSE": "-",
                                               "GLOB": "-",
                                               })
        if not opts["GLOB_RECURSE"] and not opts["GLOB"]:
            logger.warning(f"Cannot process file({args[0]} ...")
            return
        path = self.package.path / cmake_env["cwd"] if "cwd" in cmake_env else self.package.path
        matches = []
        for arg in args[1:]:
            finds = [self._trim_and_unquote(str(f)) for f in path.rglob(arg)]
            if len(finds) == 0:
                finds = [self._trim_and_unquote(str(f)) for f in self.package.path.rglob(arg)]
            logger.debug(f"Found the following matches to {arg} in {path}: {finds}")
            matches.extend(finds)
        if opts["RELATIVE"]:
            # convert path to be relative
            relative = self.package.path / opts["RELATIVE"]
            matches = [str(Path(m).relative_to(relative)) for m in matches]
        cmake_env[args[0]] = ";".join(matches)
        logger.debug(f"Set {args[0]} to {cmake_env[args[0]]}")

    @cmake_command
    def get_filename_component(
            self,
            cmake_env: dict[str, str],
            raw_args: list[str],
    ) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"DIRECTORY": "-",
             "NAME": "-",
             "EXT": "-",
             "NAME_WE": "-",
             "LAST_EXT": "-",
             "NAME_WLE": "-"},
        )
        file = args[1]
        var_name = args[0]
        if opts["DIRECTORY"]:
            cmake_env[var_name] = str(Path(file).parent)
        elif opts["NAME"]:
            cmake_env[var_name] = Path(file).name
        elif opts["EXT"]:
            cmake_env[var_name] = "." + ".".join(Path(file).name.split(".")[1:])
        elif opts["NAME_WE"]:
            cmake_env[var_name] = Path(file).name.split(".")[0]
        elif opts["LAST_EXT"]:
            cmake_env[var_name] = Path(file).suffix
        elif opts["NAME_WLE"]:
            cmake_env[var_name] = Path(file).stem
        else:
            cmake_env[var_name] = file



    @cmake_command
    def add_subdirectory(
            self,
            cmake_env: dict[str, str],
            raw_args: list[str],
    ) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"EXCLUDE_FROM_ALL": "-"},
        )
        if opts["EXCLUDE_FROM_ALL"]:
            return
        if len(args) == 0 or (len(args) > 0 and args[0] == ""):
            # Empty argument, just return
            return
        new_env = cmake_env.copy()
        new_env["cwd"] = str(Path(cmake_env.get("cwd", ".")) / args[0])
        new_env["PROJECT_SOURCE_DIR"] = str(Path(cmake_env.get("CMAKE_SOURCE_DIR", ".")) / args[0])
        new_env["CMAKE_CURRENT_SOURCE_DIR"] = new_env["cwd"]
        cmakelists_path = self.package.path / new_env["cwd"] / "CMakeLists.txt"
        new_env["cmakelists"] = str(cmakelists_path)
        logger.info(f"Processing {cmakelists_path!s}")
        with cmakelists_path.open() as f:
            contents = f.read()
        sub_cmake = self.__class__(self.package.path)
        included_pacakge_instances = sub_cmake._process_cmake_contents(contents, new_env)
        self.libraries_for.update(sub_cmake.libraries_for)
        self.executables.update(
            **{s: included_pacakge_instances.targets[s] for s in included_pacakge_instances.targets})

    @aliased_cmake_command("add_executable", "cuda_add_executable")
    def add_executable(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"EXCLUDE_FROM_ALL": "-"},
        )
        if opts["EXCLUDE_FROM_ALL"]:
            return
        name = args[0]
        sources: set[Path] = set()
        for source in args[1:]:
            if source in self.executables:
                sources.update(self.executables[source].sources)
            else:
                real_src = self._resolve_to_real_file(source, self.package.path, cmake_env)
                if real_src:
                    sources.add(real_src)
                else:
                    logger.warning(f"'{source} did not resolve to a real file.")
        logger.debug(f"Adding C++ sources for {name}")
        self.executables[name] = CMakeBinaryTarget(
            name=name,
            language=SourceLanguage.CXX,
            sources=sources,
            includes=cmake_env["INCLUDE_DIRECTORIES"].split(" ") if "INCLUDE_DIRECTORIES" in cmake_env else [],
            libraries=[],
            restrict_to_paths=self.package_paths(),
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=cmake_env["cmakelists_line"],
        )

    @cmake_command
    def target_link_libraries(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        opts, args = self._cmake_argparse(raw_args, {})
        executable = args[0]
        libraries = args[1:]
        self.libraries_for[executable] = self.libraries_for.get(executable, []) + libraries

    @cmake_command
    def include_directories(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"AFTER": "-",
             "BEFORE": "-",
             "SYSTEM": "-"},
        )
        paths_to_include = [dir_ for dir_ in args if not Path(dir_).is_absolute()]
        if len(paths_to_include) > 0:
            if opts["AFTER"] or opts["BEFORE"] or opts["SYSTEM"]:
                logger.warning("include_directors AFTER, BEFORE, SYSTEM not supported")
            if "INCLUDE_DIRECTORIES" not in cmake_env:
                cmake_env["INCLUDE_DIRECTORIES"] = ""
            cmake_env["INCLUDE_DIRECTORIES"] = " ".join(
                cmake_env["INCLUDE_DIRECTORIES"].split(" ") + paths_to_include)

    @aliased_cmake_command("add_library", "cuda_add_library")  # type: ignore
    def add_library(
            self,
            cmake_env: dict[str, t.Any],
            raw_args: list[str],
    ) -> None:
        opts, args = self._cmake_argparse(
            raw_args,
            {"SHARED": "-",
             "STATIC": "-",
             "MODULE": "-",
             "EXCLUDE_FROM_ALL": "-",
             },
        )
        if opts["EXCLUDE_FROM_ALL"]:
            return
        name = args[0]
        sources: set[Path] = set()
        for source in args[1:]:
            if source in self.executables:
                sources.update(self.executables[source].sources)
            else:
                real_src = self._resolve_to_real_file(source, self.package.path, cmake_env)
                if real_src:
                    sources.add(real_src)
                else:
                    logger.warning(f"'{source} did not resolve to a real file.")
        logger.debug(f"Adding C++ library {name}")
        self.executables[name] = IncompleteCMakeLibraryTarget(
            name,
            SourceLanguage.CXX,
            sources,
            cmake_env["INCLUDE_DIRECTORIES"].split(" ") if "INCLUDE_DIRECTORIES" in cmake_env else [],
            self.package_paths(),
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=cmake_env["cmakelists_line"],
        )

    @cmake_command
    def configure_file(
            self,
            cmake_env: dict[str, t.Any],
            rawargs: list[str],
    ) -> None:
        _opts, args = self._cmake_argparse(rawargs, {"NO_SOURCE_PERMISSIONS": "-",
                                               "USE_SOURCE_PERMISSIONS": "-",
                                               "COPY_ONLY": "-",
                                               "ESCAPE_QUOTES": "-",
                                               "@ONLY": "-",
                                               "NEWLINE_STYLE": "?",
                                               "FILE_PERMISSIONS": "?"})
        # Writing to the container doesn't persist, and so generated sources
        # aren't able to be included. Put this in a list so that we can remember them
        # and not try to resolve them to real files
        if len(args) > 0:
            # Ret rid of the parameter and just use the files
            args = args[1:]
        if len(args) > 0:
            self._files_generated_by_cmake.union(args)
        else:
            # We warn because we ignore generated files
            logger.warning(f"'{cmake_env['cmakelists']}' has no target for 'configure_fle({rawargs})")

    def _trim_and_unquote(self, s: str) -> str:
        s = s.strip()
        is_single_quoted = s.startswith("'") and s.endswith("'")
        is_double_quoted = s.startswith('"') and s.endswith('"')
        if is_single_quoted or is_double_quoted:
            s = s[1:-1]
        return s

    def _resolve_to_real_file(
            self,
            filename: str,
            package: Path,
            cmake_env: dict[str, str],
    ) -> Path | None:
        if filename in self._files_generated_by_cmake:
            return None
        real_filename = Path(filename)
        if "cwd" in cmake_env:
            real_filename = Path(cmake_env["cwd"]) / filename
        if not (package / real_filename).is_file():
            parent = real_filename.parent
            try:
                all_files = (package / parent).glob("*")
                matching_files = [f for f in all_files if str(f).startswith(str(real_filename.name))]
                if len(matching_files) != 1:
                    logger.error(f"Only one file should match '{real_filename!s}'. "
                                 f"Currently {len(matching_files)} files do: {matching_files}")
                    self._files_not_resolved.append(FileInformation(filename=filename,
                                                                    cmake_file=Path(cmake_env["cmakelists"]),
                                                                    cmake_line_no=int(cmake_env["cmakelists_line"])))
                    return None
                real_filename = parent / matching_files[0]
            except Exception:
                logger.error(
                    f"Error finding real file matching {real_filename} "
                    f"in {package / parent!s}")
                logger.error(cmake_env)
                raise
        return real_filename

    @cmake_command
    def pluginlib_export_plugin_description_file(self, cmake_env: dict[str, t.Any], raw_args: list[str]) -> None:
        # https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Pluginlib.html
        _opts, args = self._cmake_argparse(raw_args, {})
        self.plugin_references.append(CMakePluginReference(
            base_class_package=args[0],
            plugin_xml=args[1],
            cmakelists_file=cmake_env["cmakelists"],
            cmakelists_line=int(cmake_env["cmakelists_line"])
        ))
