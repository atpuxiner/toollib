"""
@author axiner
@version v1.0.0
@created 2022/4/30 13:20
@abstract
@description
@history
"""
import os

from toollib import utils
from toollib.tcli.base import BaseCmd
from toollib.common import constor
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set-conda',
            desc='设置conda源',
            optional={self.set_conda: None}
        )
        return options

    def set_conda(self):
        _home = utils.home()
        conf_file = os.path.join(_home, '.condarc')
        print(f'Writing to {conf_file}')
        with open(conf_file, mode='wb') as fp:
            fp.write(constor.conda_conf)
