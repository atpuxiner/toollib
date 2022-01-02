"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract
@description
@history
"""
from json import dumps, loads


class ToolUtils(object):

    @staticmethod
    def json(data, loadordumps="loads", default=None, *args, **kwargs):
        """json loads or dumps"""
        if not data:
            data = default or data
        else:
            if loadordumps == "loads":
                data = loads(data, *args, **kwargs)
            elif loadordumps == "dumps":
                data = dumps(data, *args, **kwargs)
            else:
                raise ValueError("Only select from: [loads, dumps]")
        return data
