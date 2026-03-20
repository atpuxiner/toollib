"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""

from collections.abc import Callable, Iterable
from typing import Any

from toollib.validator import Attr


class Arg:
    def __init__(
        self,
        *name_or_flags: str,
        action: str | None = None,
        nargs: int | str | None = None,
        const: Any = None,
        default: Any = None,
        type: type | None = None,
        choices: Iterable | None = None,
        required: bool = False,
        help: str | None = None,
        metavar: str | tuple[str] | None = None,
        dest: str | None = None,
        version: str | None = None,
        **kwargs,
    ):
        self.name_or_flags = name_or_flags
        self.action = action
        self.nargs = nargs
        self.const = const
        self.default = default
        self.type = type
        self.choices = choices
        self.required = required
        self.help = help
        self.metavar = metavar
        self.dest = dest
        self.version = version
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def parse_arg(self):
        arg = {k: v for k, v in self.__dict__.items() if v}
        return arg.pop("name_or_flags"), arg


def check_optional(optional):
    for subcmd, args in optional.items():
        if callable(subcmd) is False:
            raise TypeError('"subcmd" only supported: Callable')
        errmsg = '"optional" value only supported: list[Arg] | None'
        if not isinstance(args, (list, type(None))):
            raise TypeError(errmsg)
        if args:
            for arg in args:
                if not isinstance(arg, Arg):
                    raise TypeError(errmsg)


class Options:
    name: str = Attr("name", str, required=True)
    desc: str = Attr("desc", str, required=True)
    optional: dict[Callable, list[Arg] | None] = Attr(
        "optional",
        dict,
        required=True,
        callback=check_optional,
    )

    def __init__(self, name, desc, optional):
        self.name = name
        self.desc = desc
        self.optional = optional

    @property
    def subcmds(self) -> dict:
        return {item[0].__name__: item for item in self.optional.items()}
