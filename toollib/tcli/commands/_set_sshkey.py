"""
@author axiner
@version v1.0.0
@created 2022/5/4 9:17
@abstract
@description
@history
"""
import os
import stat
import subprocess
import sys

from toollib.decorator import sys_required
from toollib.tcli import here
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set-sshkey',
            desc='设置ssh免密',
            optional={
                self.set_sshkey: [
                    Arg('-i', '--infos', required=True, type=str, help='"ip1,user1,pass1,port1 ip2,user2,pass2,port2 ..."|也可指定文件:一行一个'),
                    Arg('--sysname', type=str, help='系统名称（以防自动获取不精确）'),
                ]}
        )
        return options

    @sys_required(r'Ubuntu|Debian|CentOS|RedHat|Rocky')
    def set_sshkey(self):
        infos = self.parse_args.infos.strip()
        if not infos or infos == "''":
            sys.stderr.write('ERROR: -i/--infos: 不能为空\n')
            sys.exit(1)
        shpath = here.joinpath('commands/plugins/set_sshkey.sh').as_posix()
        if not os.access(shpath, os.X_OK):
            os.chmod(shpath, os.stat(shpath).st_mode | stat.S_IEXEC)
        cmd = ['/bin/bash', shpath, infos]
        subprocess.run(cmd)
