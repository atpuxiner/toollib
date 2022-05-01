"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:31
@abstract
@description
@history
"""
import sys
from pathlib import Path
from platform import platform

from toollib import utils
from toollib.decorator import sys_required
from toollib.tcli.base import BaseCmd
from toollib.tcli.commands import byter
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set pip',
            desc='设置pip源',
            optional={self.setpip: None}
        )
        return options

    @sys_required()
    def setpip(self):
        sys.stdout.write('设置镜像源.....\n')
        _home = utils.home()
        if platform().find('Windows') != -1:
            conf_file = Path(_home, 'pip', 'pip.ini')
        else:
            conf_file = Path(_home, '.pip', 'pip.conf')
        conf_file.parent.mkdir(parents=True, exist_ok=True)
        with open(conf_file, mode='wb') as f:
            f.write(byter.pip_conf)
            sys.stdout.write(f'to Path>>> {conf_file.as_posix()}\n')
            sys.stdout.write(byter.pip_conf.decode('utf8'))
            sys.stdout.write('\n设置完成\n')
