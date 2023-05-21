"""
@author axiner
@version v1.0.0
@created 2023/4/7 16:12
@abstract
@description
@history
"""
import sys

from toollib.py2pyder import Py2Pyder
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='py2pyd',
            desc='py转pyd',
            optional={self.py2pyd: [
                Arg('-s', '--src', required=True, type=str, help='源（py目录或文件）'),
                Arg('-p', '--postfix', type=str, help='后缀（默认为Pyd）'),
                Arg('-e', '--exclude', type=str, help='排除编译（适用正则，使用管道等注意加引号）'),
                Arg('-i', '--ignore', type=str, default='.git,.idea,__pycache__', help='忽略复制（多个逗号隔开）'),
                Arg('-c', '--clean', action='store_true', help='清理临时'),
            ]}
        )
        return options

    def py2pyd(self):
        src = self.parse_args.src
        if not src or src == "''":
            sys.stderr.write('ERROR: -s/--src: 不能为空\n')
            sys.exit(1)
        postfix = self.parse_args.postfix
        exclude = self.parse_args.exclude
        ignore = self.parse_args.ignore
        clean = self.parse_args.clean
        py2pyder = Py2Pyder(src, postfix, exclude, ignore, clean)
        py2pyder.run()
