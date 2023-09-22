"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:31
@abstract
@description
@history
"""
import subprocess
import sys

from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='set-pip',
            desc='设置pip源',
            optional={self.set_pip: [
                Arg('-s', '--src', default='tsinghua', type=str, help='源（tsinghua|aliyun|bfsu|douban|pypi）'),
                Arg('-t', '--timeout', default=120, type=int, help='超时'),
            ]}
        )
        return options

    def set_pip(self):
        src = self.parse_args.src
        timeout = self.parse_args.timeout
        srcs = {
            'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple/',
            'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',
            'bfsu': 'https://mirrors.bfsu.edu.cn/pypi/web/simple/',
            'douban': 'https://pypi.doubanio.com/simple/',
            'pypi': 'https://pypi.python.org/simple/',
        }
        set_src = srcs.get(src)
        if not set_src:
            print(f'ERROR: {src}：暂未收录，请选择源（tsinghua|aliyun|bfsu|douban|pypi）')
            sys.exit(1)
        subprocess.run(f'pip config set global.timeout {timeout}', shell=True, capture_output=True)
        subprocess.run(f'pip config set global.index-url {set_src}', shell=True)
