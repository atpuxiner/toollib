"""
@author axiner
@version v1.0.0
@created 2022/1/2 14:47
@abstract
@description
@history
"""
from threading import Lock

__all__ = ["Singleton"]


class Singleton(type):
    """单例模式"""

    __instance_lock = Lock()

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super(Singleton, cls).__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__instance_lock:
                if cls.__instance is None:
                    cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instance
