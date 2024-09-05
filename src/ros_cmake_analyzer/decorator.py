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
        for method in attrs.values():
            if hasattr(method, "commands"):
                for command in method.commands:
                    cls._handlers[command] = method


TCMakeFunction = t.Callable[[t.Any, dict[str, t.Any], list[str]], None]  # TODO: Self?


def aliased_cmake_command(*commands: str) -> t.Callable[[TCMakeFunction], TCMakeFunction]:
    """Decorator for cmake directive handlers.

    Methods in a class are registered as cmake directives either by decorating them by @cmake_command or by adding
    a commands attribute to the decorator for the command to registered by. For example, @cmake_command(["list"])
    registers the decorated method as handling "list" directives.

    :param commands: *str
        List of cmake directives to register the decorated method with.
    :return: TCMakeFunction
        The registered cmake directive handler.
    """

    def wrapper(fn: TCMakeFunction) -> TCMakeFunction:
        fn.commands = commands
        return fn

    return wrapper


def cmake_command(func: TCMakeFunction) -> TCMakeFunction:
    func.commands = (func.__name__, )
    return func

#
# def cmake_command(arg: TCMakeFunction | list[str] | None = None) -> TCMakeFunction:
#     """Decorator for cmake directive handlers.
#
#     Methods in a class are registered as cmake directives either by decorating them by @cmake_command or by adding
#     a commands attribute to the decorator for the command to registered by. For example, @cmake_command(["list"])
#     registers the decorated method as handling "list" directives.
#
#     :param arg: CMakeFunctionT | list[str]
#         If no parameter is passed to the directive, the function is passed. If the parameter is passed then
#         it is used as the command names
#     :return:  CMakeFunctionT
#         The registered method
#     """
#     if callable(arg):
#         arg.command = True
#         return arg
#
#     def c2(fn: TCMakeFunction) -> TCMakeFunction:
#         fn.command = True
#         fn.commands = arg
#         return fn
#     return c2  # type: ignore
