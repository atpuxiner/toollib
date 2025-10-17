import os


def home() -> str:
    """
    家目录

    e.g.::

        h = utils.home()

        +++++[更多详见参数或源码]+++++
    """
    return os.environ.get("HOME") or os.path.join(os.environ.get("HOMEDRIVE"), os.environ.get("HOMEPATH"))
