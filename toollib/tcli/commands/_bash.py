"""
@author axiner
@version v1.0.0
@created 2023/5/23 14:51
@abstract
@description
@history
"""
import re
import sys

from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins import bash_tpl
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='bash',
            desc='bash模板',
            optional={self.tpl2bash: [
                Arg('-f', '--file', required=True, type=str, help='文件'),
                Arg('-c', '--cmds', required=True, type=str, help='命令'),
                Arg('-o', '--opts', type=str, help='选项'),
            ]}
        )
        return options

    def tpl2bash(self):
        file = self.parse_args.file
        cmds = self.parse_args.cmds
        opts = self.parse_args.opts
        short_opts, long_opts, default_false_opts, all_opts, all_cmds, all_funcs = '', '', '', '', '', ''
        if not re.match(r'^[^,\s]+(,[^,\s]+)*$', cmds):
            print(f'ERROR: {cmds}: 格式错误（多个用`,`隔开，且不能包含空格）')
            sys.exit(1)
        for item in opts.split(',') if opts else '':
            item = item.strip()
            if not item or item in ['h/help', 'h', 'help', 'version']: continue
            opts_error_msg = f'ERROR: {item}: 格式错误（不能包含空格，短选项单字符，长选项多字符，后可接`:`表示需要值，如：s/src:）'
            if '/' in item:
                if not re.match(r'^[^/\s](/[^/\s]{2,})?:?$', item):
                    print(opts_error_msg)
                    sys.exit(1)
            else:
                if not re.match(r'^\S+$', item):
                    print(opts_error_msg)
                    sys.exit(1)
            sl = item.rstrip(':').split('/')
            sl_len = len(sl)
            var = bash_tpl.VAR_PREFIX + sl[-1].upper()
            sc, lc = 0, 0
            if sl_len == 1:
                if len(sl[-1]) == 1:
                    sc = 1
                    short_opts += sl[0]
                    opt_text = bash_tpl.OPT_DEFAULT.replace('{opt}', '-' + sl[0]).replace('{var}', var)
                else:
                    lc = 1
                    long_opts += f',{sl[0]}'
                    opt_text = bash_tpl.OPT_DEFAULT.replace('{opt}', f'--{sl[0]}').replace('{var}', var)
            else:
                sc, lc = 1, 1
                short_opts += sl[0]
                long_opts += f',{sl[1]}'
                opt_text = bash_tpl.OPT_DEFAULT.replace('{opt}', f'-{sl[0]}|--{sl[1]}').replace('{var}', var)
            if item[-1] == ':':
                if sc:
                    short_opts += ':'
                if lc:
                    long_opts += ':'
                opt_text = opt_text.replace('{value}', '$2')
            else:
                opt_text = opt_text.replace('{value}', 'true').replace('shift 2', 'shift')
                default_false_opts += f'{var}=false\n'
            all_opts += opt_text
        for cmd in cmds.split(','):
            all_funcs += bash_tpl.FUNC_DEFAULT.format(cmd=cmd)
            all_cmds += bash_tpl.CMD_DEFAULT.format(cmd=cmd)

        print(f'Writing to {file}')
        with open(file, 'w', encoding='utf8') as fp:
            fp.write(
                bash_tpl.BASH_TPL.replace(
                    '@SHORT_OPTS', short_opts
                ).replace(
                    '@LONG_OPTS', long_opts.rstrip(',')
                ).replace(
                    '@DEFAULT_FALSE_OPTS', default_false_opts
                ).replace(
                    '@ALL_OPTS', all_opts
                ).replace(
                    '@ALL_FUNCS', all_funcs.rstrip()
                ).replace(
                    '@ALL_CMDS', all_cmds.rstrip()
                ).replace(
                    '@CMDS_STR', cmds.replace(',', '|')
                )
            )
