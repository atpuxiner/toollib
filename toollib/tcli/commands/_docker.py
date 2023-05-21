"""
@author axiner
@version v1.0.0
@created 2022/5/11 21:44
@abstract
@description
@history
"""
import json
import os
import re
import subprocess
import sys

from toollib.common import constor
from toollib.decorator import sys_required
from toollib.tcli import here
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()
        self.yml_path = here.joinpath('commands', 'plugins', 'docker-compose.yml').as_posix()

    def add_options(self):
        options = Options(
            name='docker操作',
            desc='docker操作',
            optional={
                self.install: [
                    Arg('--sysname', type=str, help='系统名称（以防自动获取不精确）'),
                ],
                self.set_daemon: [
                    Arg('--sysname', type=str, help='系统名称（以防自动获取不精确）'),
                ],
                self.toyml: [
                    Arg('-n', '--names', required=True, type=str, help='服务名称（多个用逗号隔开）'),
                    Arg('-o', '--outdir', type=str, help='输出目录'),
                    Arg('-f', '--filename', type=str, help='文件名称'),
                ],
            }
        )
        return options

    @sys_required(r'Ubuntu|Debian|CentOS|RedHat|Rocky')
    def install(self):
        try:
            subprocess.run(['docker', '-v'], stderr=subprocess.DEVNULL, encoding='utf8')
            print('WARNING: Docker already exist')
        except Exception:
            cmd = 'curl -sSL https://get.daocloud.io/docker | sh'
            subprocess.run(cmd, shell=True)

    @sys_required(r'Ubuntu|Debian|CentOS|RedHat|Rocky')
    def set_daemon(self):
        print('设置daemon配置.....')
        subprocess.run(['systemctl', 'stop', 'docker'])
        docker_conf_dir = '/etc/docker'
        if not os.path.isdir(docker_conf_dir):
            os.mkdir(docker_conf_dir)
        docker_conf_file = os.path.join(docker_conf_dir, 'daemon.json')
        with open(docker_conf_file, 'w') as fp:
            fp.write(json.dumps(constor.docker_daemon, indent=2))
            print(f'to Path >>> {docker_conf_file}')
            print('设置完成')
        subprocess.run(['systemctl', 'start', 'docker'])

    def toyml(self):
        names = self.parse_args.names
        if not names or names == "''":
            sys.stderr.write('ERROR: -n/--names: 不能为空\n')
            sys.exit(1)
        if names == 'list':
            self._yml_list()
            sys.exit()
        outdir = self.parse_args.outdir
        if outdir:
            if not os.path.isdir(outdir):
                sys.stderr.write(f'ERROR: {outdir}: 目录不存在\n')
                sys.exit(1)
        else:
            outdir = os.getcwd()
        filename = self.parse_args.filename or 'docker-compose.yml'
        yml_path = os.path.join(outdir, filename)
        c = 0
        for name, yml_conf in self._search_yml_conf(names):
            if not yml_conf:
                print(f'{name}: 抱歉暂未收录')
            else:
                mode = 'w'
                if os.path.isfile(yml_path) and os.path.getsize(yml_path):
                    with open(yml_path, 'r') as fp:
                        ctx = fp.read()
                        if ctx.strip():
                            mode = 'a'
                            if re.search(rf"\r?\n\s\s{name}(-\w*)?:\s*\r?\n", ctx):
                                print(f'{name}: `{yml_path}`疑似存在')
                                continue
                if mode == 'a':
                    yml_conf = '\n' + yml_conf
                else:
                    yml_conf = 'version: "3.8"\nservices:\n' + yml_conf
                with open(yml_path, mode) as fp:
                    fp.write(yml_conf)
                    print(f'{name}: `{yml_path}`写入成功')
                    c += 1
        if c:
            print('后续可通过`docker compose`命令管理服务（请按需修改配置）')

    def _search_yml_conf(self, names: str):
        with open(self.yml_path, 'r') as fp:
            yml_text = fp.read()
            if names == 'all':
                namelist = self._findall_services()
            else:
                namelist = names.split(',')
            for n in namelist:
                regex = r'\r?\n(\s{2}' + n + r'(-\w*)?:\s*.*?)(?=\r?\n\s*\r?\n|$)'
                matches = re.search(regex, yml_text, re.DOTALL)
                if matches:
                    yield n, matches.group(0).rstrip()
                else:
                    yield n, None

    def _yml_list(self):
        services = self._findall_services() or ['正在努力收录中...']
        services.insert(0, '已收录的服务:')
        resp_text = '\n  '.join(services)
        print(resp_text)

    def _findall_services(self) -> list:
        with open(self.yml_path, 'r') as fp:
            services = re.findall(r"^\r?\n\s{2}(\w+)(?:-\w*)?:\s*\r?\n", fp.read(), re.MULTILINE)
            return services
