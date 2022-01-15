"""
@author axiner
@version v1.0.0
@created 2021/12/12 13:14
@abstract This is a tool library.
@description
@history
"""
from .libs import decorator as decorator
from .libs.g import G
from .libs.singleton import Singleton
from .libs import utils as utils

__all__ = [
    "decorator",
    "G",
    "Singleton",
    "utils",
]

__version__ = "2022.01.13"
