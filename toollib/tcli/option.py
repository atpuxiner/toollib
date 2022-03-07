"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""
from toollib.validator import Typer, choicer


def check_callcmd(value):
    if callable(value) is False:
        raise TypeError('"callcmd" only supported: Callable')


def check_args(value):
    for item in value:
        if not isinstance(item, dict):
            raise TypeError('"args" only supported: dict')
        if item.get('required'):
            choicer(str(item.get('required')), ['True', 'False', '-1'], 'required',
                    '"required" only supported: [True, False, -1]')


class Option:
    name: str = Typer('name', str)
    callcmd = Typer('callcmd', func=check_callcmd)
    desc: str = Typer('desc', str)
    args: list = Typer('args', list, required=False, func=check_args)

    def __init__(self, name, desc, callcmd, args=None):
        self.name = name
        self.desc = desc
        self.callcmd = callcmd
        self.args = args
