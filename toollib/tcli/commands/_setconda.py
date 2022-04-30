"""
@author axiner
@version v1.0.0
@created 2022/4/30 13:20
@abstract
@description
@history
"""
import sys
from pathlib import Path

from toollib import utils
from toollib.tcli import sys_required
from toollib.tcli.base import BaseCmd
from toollib.tcli.commands import byter
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set conda',
            desc='设置conda源',
            optional={self.setconda: None}
        )
        return options

    @sys_required()
    def setconda(self):
        sys.stdout.write('设置镜像源.....\n')
        _home = utils.home()
        conf_file = Path(_home, '.condarc')
        with open(conf_file, mode='wb') as f:
            f.write(byter.conda_conf)
            sys.stdout.write(f'to Path>>> {conf_file.as_posix()}\n')
            sys.stdout.write(byter.conda_conf.decode('utf8'))
            sys.stdout.write('\n设置完成\n')
