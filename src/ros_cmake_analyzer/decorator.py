from __future__ import annotations

import abc
import typing as t


class CommandHandlerType(type, abc.ABC):
    """A metaclass that stores CMake command handlers.

    Stores the handlers either by the method name, or by the names specified in 'commands' attribute.
    """
    def __init__(cls, name: str, bases: t.Any, attrs: dict[str, t.Any]) -> None:  # noqa: ARG003, ANN401
        super().__init__(cls)
        cls._handlers = {}
        for name, method in attrs.items():
            if hasattr(method, "command"):
                if hasattr(method, "commands"):
                    for command in method.commands:
                        cls._handlers[command] = method
                else:
                    cls._handlers[name] = method


CMakeFunctionT = t.Callable[[t.Any, dict[str, t.Any], list[str]], None]  # TODO: Self?


def cmake_command(arg: CMakeFunctionT | list[str]) -> CMakeFunctionT:
    """Decorator for cmake directive handlers.

    Methods in a class are registered as cmake directives either by decorating them by @cmake_command or by adding
    a commands attribute to the decorator for the command to registered by. For example, @cmake_command(["list"])
    registers the decorated method as handling "list" directives.

    :param arg: CMakeFunctionT | list[str]
        If no parameter is passed to the directive, the function is passed. If the parameter is passed then
        it is used as the command names
    :return:  CMakeFunctionT
        The registered method
    """
    if callable(arg):
        arg.command = True
        return arg

    def c2(fn: CMakeFunctionT) -> CMakeFunctionT:
        fn.command = True
        fn.commands = arg
        return fn
    return c2  # type: ignore
