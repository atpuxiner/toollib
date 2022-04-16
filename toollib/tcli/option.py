"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""
from toollib.validator import Attr, choicer


def check_callcmd(value):
    if callable(value) is False:
        raise TypeError('"callcmd" only supported: Callable')


def check_args(value):
    for item in value:
        if not isinstance(item, dict):
            raise TypeError('"args" only supported: dict')
        if item.get('required'):
            choicer(
                str(item.get('required')),
                choices=['True', 'False', '-1'],
                lable='required',
                errmsg='"required" only supported: [True, False, -1]')


class Option:
    name: str = Attr('name', str, required=True)
    callcmd = Attr('callcmd', required=True, callback=check_callcmd)
    desc: str = Attr('desc', str, required=True)
    args: list = Attr('args', list, callback=check_args)

    def __init__(self, name, desc, callcmd, args=None):
        self.name = name
        self.desc = desc
        self.callcmd = callcmd
        self.args = args or []
