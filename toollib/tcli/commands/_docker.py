"""
@author axiner
@version v1.0.0
@created 2022/5/11 21:44
@abstract
@description
@history
"""
import sys

from toollib import utils
from toollib.decorator import sys_required
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='docker操作',
            desc='docker操作',
            optional={
                self.install: None,
                self.start: [
                    Arg('-n', '--name', required=True, type=str, help='镜像名称'),
                ],
            }
        )
        return options

    @sys_required('centos|\.el\d|ubuntu', errmsg='centos|el|ubuntu')
    def install(self):
        cmd = 'curl -sSL https://get.daocloud.io/docker | sh'
        p = utils.syscmd(cmd)
        out, err = p.communicate()
        if out:
            sys.stdout.write(u'{0}'.format(out.decode('utf-8')))
        if err:
            sys.stderr.write(u'{0}'.format(err.decode('utf-8')))

    @sys_required('centos|\.el\d|ubuntu', errmsg='centos|el|ubuntu')
    def start(self):
        sys.stdout.write('努力实现中...')
