import platform
import re
import subprocess


def sysname() -> str:
    """
    系统名称

    e.g.::

        s = utils.sysname()

        +++++[更多详见参数或源码]+++++
    """
    name = platform.uname().system
    if name == 'Linux':
        try:
            result = subprocess.run(
                'cat /etc/*-release',
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                encoding='utf8',
                shell=True,
            )
            r = re.search(r'[\n\s]+ID=(.*?)[\n\s]+', result.stdout)
            name = r.group(1) if r else name
        except Exception:
            pass
    elif name == 'Darwin':
        name = 'macOS'
    return name.lower().replace(' ', '')
