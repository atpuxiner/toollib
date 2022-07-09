"""
@author axiner
@version v1.0.0
@created 2022/5/11 21:44
@abstract
@description
@history
"""
import sys

from toollib.tcli import here

from toollib import utils
from toollib.decorator import sys_required
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set yum',
            desc='设置yum源',
            optional={self.set_yum: None}
        )
        return options

    @sys_required('centos|\.el\d', errmsg='centos|el')
    def set_yum(self):
        shb = here.joinpath('commands/plugins/set_yum.sh.x')
        cmd = f'chmod u+x {shb} && {shb}'
        p = utils.syscmd(cmd)
        out, err = p.communicate()
        if out:
            sys.stdout.write(u'{0}'.format(out.decode('utf-8')))
        if err:
            sys.stderr.write(u'{0}'.format(err.decode('utf-8')))
