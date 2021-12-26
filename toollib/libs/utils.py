"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract
@description
@history
"""
import json
import threading


class Utils(object):

    @staticmethod
    def json(data, loadordumps="loads", default=None, *args, **kwargs):
        """json loads or dumps"""
        if not data:
            data = default or data
        else:
            if loadordumps == "loads":
                data = json.loads(data, *args, **kwargs)
            elif loadordumps == "dumps":
                data = json.dumps(data, *args, **kwargs)
            else:
                raise ValueError("Only select from: [loads, dumps]")
        return data


class SingletonType(type):

    _instance_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instance
