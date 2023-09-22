"""
@author axiner
@version v1.0.0
@created 2022/5/11 21:44
@abstract
@description
@history
"""
import subprocess
import sys

from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins.aliyun_mirrors import mirrors_cmds
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set-mirrors',
            desc='设置镜像源',
            optional={self.set_mirrors: [
                Arg('-s', '--sysname', required=True, type=str, help='系统名称（包括版本号）'),
            ]}
        )
        return options

    def set_mirrors(self):
        curr_sysname = self.parse_args.sysname.strip().lower()
        if not curr_sysname or curr_sysname == "''":
            sys.stderr.write('ERROR: -s/--sysname: 不能为空\n')
            sys.exit(1)
        cmds = mirrors_cmds.get(curr_sysname)
        if not cmds:
            print(f'{curr_sysname}: 抱歉暂未收录')
            mirrors_sysname = list(mirrors_cmds.keys())
            mirrors_sysname.insert(0, '已收录的系统版本：')
            print('\n  '.join(mirrors_sysname))
            sys.exit(1)
        for cmd in cmds:
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                sys.stderr.write('Failed（请检查网络或其他）')
                sys.exit(1)
        print('提醒：若更新失败请检查网络是否畅通')
