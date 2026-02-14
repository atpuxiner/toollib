"""
@author axiner
@version v1.0.0
@created 2023/4/7 16:12
@abstract
@description
@history
"""
import sys

from toollib.pyd import PydPacker
from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def add_options(self):
        options = Options(
            name='pyd打包',
            desc='pyd打包',
            optional={self.pydpack: [
                Arg('-s', '--src', required=True, type=str, help='源（py目录或文件）'),
                Arg('-e', '--exclude', type=str, help='排除编译（正则表达式，使用管道等注意加引号）'),
                Arg('-i', '--ignore', default='.git|.idea|.vscode|__pycache__', type=str, help='忽略复制（正则表达式，使用管道等注意加引号）'),
                Arg('--ext-suffix', action='store_true', help='是否保留扩展后缀（默认不保留）'),
                Arg('--clean', action='store_true', help='是否清理（默认不清理）'),
            ]}
        )
        return options

    def pydpack(self):
        src = self.parse_args.src.strip()
        if not src or src == "''":
            sys.stderr.write('ERROR: -s/--src: 不能为空\n')
            sys.exit(1)
        packer = PydPacker(
            src=src,
            exclude=self.parse_args.exclude,
            ignore=self.parse_args.ignore,
            keep_ext_suffix=self.parse_args.ext_suffix,
            is_clean=self.parse_args.clean,
        )
        packer.run()
