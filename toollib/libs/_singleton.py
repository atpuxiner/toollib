"""
@author axiner
@version v1.0.0
@created 2022/1/2 14:47
@abstract
@description
@history
"""
from threading import Lock


class ToolSingleton(type):
    """singleton"""

    __instance_lock = Lock()

    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "__instance"):
            with cls.__instance_lock:
                if not hasattr(cls, "__instance"):
                    cls.__instance = super(ToolSingleton, cls).__call__(*args, **kwargs)
        return cls.__instance
