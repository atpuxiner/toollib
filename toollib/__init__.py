"""
@author axiner
@version v1.0.0
@created 2021/12/12 13:14
@abstract This is a tool library.
@description
@history
"""
from .libs.decorator import Decorator
from .libs.g import G
from .libs.singleton import Singleton
from .libs.utils import Utils

__all__ = [
    "Decorator",
    "G",
    "Singleton",
    "Utils",
]
