"""
@author axiner
@version v1.0.0
@created 2022/5/4 9:17
@abstract
@description
@history
"""
import re
import sys
from pathlib import Path

from toollib import utils, regexp
from toollib.decorator import sys_required
from toollib.tcli import here
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='ssh key',
            desc='ssh免密登录配置',
            optional={
                self.set_sshkey: [
                    Arg('-u', '--user', required=True, type=str, help='用户'),
                    Arg('-p', '--passwd', required=True, type=str, help='密码'),
                    Arg('--port', default=22, type=int, help='端口'),
                    Arg('-i', '--ips', required=True, type=str,
                        help='ips, 1.多个ip可用逗号隔开；2.也可指定文件(一行一ip)'),
                ]}
        )
        return options

    @sys_required('centos|\.el\d', errmsg='centos|el')
    def set_sshkey(self):
        user = self.parse_args.user
        passwd = self.parse_args.passwd
        port = self.parse_args.port
        ips = self._parse_ips(self.parse_args.ips)
        shb = here.joinpath('commands/plugins/set_sshkey.sh.x')
        cmd = f'chmod u+x {shb} && {shb} {user} {passwd} {port} {" ".join(ips)}'
        p = utils.syscmd(cmd)
        out, err = p.communicate()
        if out:
            sys.stdout.write(u'{0}'.format(out.decode('utf-8')))
        if err:
            sys.stderr.write(u'{0}'.format(err.decode('utf-8')))

    def _parse_ips(self, ips) -> set:
        parse_ips = set()
        if Path(ips).is_file():
            with open(ips, mode='r', encoding='utf8') as fp:
                ip_list = [ip.replace('\n', '') for ip in fp.readlines() if not ip.startswith('#')]
        else:
            ip_list = ips.split(',')
        ip_list = [ip.strip() for ip in ip_list if ip.strip()]
        if not ip_list:
            raise ValueError('ips不能为空')
        for ip in ip_list:
            if not re.match(regexp.ipv4_simple, ip):
                raise ValueError('%s =>ip格式错误' % ip)
            parse_ips.add(ip)
        return parse_ips
