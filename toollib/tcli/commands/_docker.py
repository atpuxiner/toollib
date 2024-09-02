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
        self.yaml_path = here.joinpath('commands', 'plugins', 'docker-compose.yaml').as_posix()

    def add_options(self):
        options = Options(
            name='docker',
            desc='docker操作',
            optional={
                self.set_daemon: [
                    Arg('--sysname', type=str, help='系统名称（以防自动获取不精确）'),
                    Arg('--dns', action='store_true', help='是否dns配置（默认不配置）'),
                ],
                self.yaml: [
                    Arg('-n', '--names', required=True, type=str, help='服务名称（多个用逗号隔开）'),
                    Arg('-o', '--outdir', type=str, help='输出目录'),
                    Arg('-f', '--filename', type=str, help='文件名称'),
                ],
            }
        )
        return options

    @sys_required(r'Ubuntu|Debian|CentOS|RedHat|Rocky')
    def set_daemon(self):
        subprocess.run(['systemctl', 'stop', 'docker'])
        conf_dir = '/etc/docker'
        if not os.path.isdir(conf_dir):
            os.mkdir(conf_dir)
        conf_file = os.path.join(conf_dir, 'daemon.json')
        print(f'Writing to {conf_file}')
        daemon_config = {}
        if os.path.isfile(conf_file):
            with open(conf_file, 'r', encoding='utf-8') as f:
                _ftext = f.read().strip('\r\n ')
                if _ftext:
                    daemon_config = json.loads(_ftext)
        daemon_config['registry-mirrors'] = constor.docker_daemon['registry-mirrors']
        if self.parse_args.dns:
            daemon_config['dns'] = constor.docker_daemon['dns']
        with open(conf_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(daemon_config, indent=2))
        subprocess.run(['systemctl', 'start', 'docker'])

    def yaml(self):
        names = self.parse_args.names.strip()
        if not names or names == "''":
            sys.stderr.write('ERROR: -n/--names: 不能为空\n')
            sys.exit(1)
        if names == 'list':
            self._yaml_list()
            sys.exit()
        outdir = self.parse_args.outdir
        if outdir:
            if not os.path.isdir(outdir):
                sys.stderr.write(f'ERROR: {outdir}: 目录不存在\n')
                sys.exit(1)
        else:
            outdir = os.getcwd()
        filename = self.parse_args.filename or 'docker-compose.yaml'
        yaml_path = os.path.join(outdir, filename)
        c = 0
        for name, yaml_conf in self._search_yaml_conf(names):
            if not yaml_conf:
                print(f'{name}: 抱歉暂未收录')
            else:
                mode = 'w'
                if os.path.isfile(yaml_path) and os.path.getsize(yaml_path):
                    with open(yaml_path, 'r') as fp:
                        text = fp.read()
                        if text.strip():
                            mode = 'a'
                            if re.search(rf"\r?\n\s\s{name}(-\w*)?:\s*\r?\n", text):
                                print(f'{name}: `{yaml_path}`疑似存在')
                                continue
                if mode == 'a':
                    yaml_conf = '\n' + yaml_conf
                else:
                    yaml_conf = '#version: "3.9"\nservices:\n' + yaml_conf
                with open(yaml_path, mode) as fp:
                    fp.write(yaml_conf)
                    print(f'{name}: `{yaml_path}`写入成功')
                    c += 1
        if c:
            print('后续可通过`docker compose`命令管理服务（请按需修改配置）')

    def _search_yaml_conf(self, names: str):
        with open(self.yaml_path, 'r') as fp:
            yaml_text = fp.read()
            if names == 'all':
                namelist = self._findall_services()
            else:
                namelist = names.split(',')
            for n in namelist:
                regex = r'\r?\n(\s{2}' + n + r'(-\w*)?:\s*.*?)(?=\r?\n\s*\r?\n|$)'
                matches = re.search(regex, yaml_text, re.DOTALL)
                if matches:
                    yield n, matches.group(0).rstrip()
                else:
                    yield n, None

    def _yaml_list(self):
        services = self._findall_services() or ['正在努力收录中...']
        services.insert(0, '已收录的服务:')
        resp_text = '\n  '.join(services)
        print(resp_text)

    def _findall_services(self) -> list:
        with open(self.yaml_path, 'r') as fp:
            services = re.findall(r"^\r?\n\s{2}(\w+)(?:-\w*)?:\s*\r?\n", fp.read(), re.MULTILINE)
            return services
