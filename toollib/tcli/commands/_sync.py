"""
@author axiner
@version v1.0.0
@created 2022/5/2 9:35
@abstract
@description
@history
"""
from toollib.decorator import sys_required
from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins.sync import execute
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='sync',
            desc='文件同步',
            optional={
                self.sync: [
                    Arg('-s', '--src', required=True, type=str, help='源'),
                    Arg('-d', '--dest', required=True, type=str, help='目标'),
                    Arg('-i', '--ip', required=True, type=str, help='ip'),
                    Arg('-u', '--user', required=True, type=str, help='用户'),
                    Arg('-p', '--port', default=22, type=int, help='端口'),
                    Arg('--suffix', type=str, help='后缀'),
                ]}
        )
        return options

    @sys_required('centos|\.el\d', errmsg='centos|el')
    def sync(self):
        src = self.parse_args.src
        dest = self.parse_args.dest
        ip = self.parse_args.ip
        user = self.parse_args.user
        port = self.parse_args.port
        suffix = self.parse_args.suffix
        execute(src, dest, ip, user, port, suffix)
