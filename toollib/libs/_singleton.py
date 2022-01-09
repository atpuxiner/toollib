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

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super(ToolSingleton, cls).__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__instance_lock:
                if cls.__instance is None:
                    cls.__instance = super(ToolSingleton, cls).__call__(*args, **kwargs)
        return cls.__instance
