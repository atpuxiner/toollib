"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:31
@abstract
@description
@history
"""
from pathlib import Path
from platform import platform

from toollib import utils
from toollib.tcli.base import BaseCmd
from toollib.common import constor
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set-pip',
            desc='设置pip源',
            optional={self.set_pip: None}
        )
        return options

    def set_pip(self):
        print('设置镜像源.....')
        _home = utils.home()
        if platform().find('Windows') != -1:
            conf_file = Path(_home, 'pip', 'pip.ini')
        else:
            conf_file = Path(_home, '.pip', 'pip.conf')
        conf_file.parent.mkdir(parents=True, exist_ok=True)
        with open(conf_file, mode='wb') as fp:
            fp.write(constor.pip_conf)
            print(f'to Path >>> {conf_file.as_posix()}')
            print('设置完成')
