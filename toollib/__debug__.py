"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:20
@abstract
@description
@history
"""
from pathlib import Path

here = Path(__file__).absolute().parent


def t001():
    print(here)


if __name__ == "__main__":
    t001()
