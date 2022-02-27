"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""
import sys
from argparse import ArgumentParser, Namespace

import typing as t

from toollib.tcli import Conf
from toollib.tcli.option import Option

_OptionsType = t.Union[t.List[Option], Option]


class BaseCmd:

    argv: list
    options: _OptionsType
    parse_args: Namespace
    helper: str

    def add_options(self) -> _OptionsType:
        raise NotImplementedError('subclasses of BaseCmd must provide a add_options() method')

    def load_options(self):
        options = self.add_options()
        errmsg = '"add_options()" return type only supported: Union[List[Option], Option]'
        if not isinstance(options, (list, Option)):
            raise TypeError(errmsg)
        if isinstance(options, list):
            for opt in options:
                if not isinstance(opt, Option):
                    raise TypeError(errmsg)
        self.options = options

    @property
    def load_callcmd(self) -> t.Callable:
        self.load_options()
        self.help()
        if isinstance(self.options, list):
            sys_opts = [item.name for item in self.options]
            if not self.argv[2:]:
                sys.stderr.write('ERROR: option is required\n')
                sys.stderr.write(self.helper)
                sys.exit(1)
            user_opt = self.argv[2]
            # 判断是不是存在参数，存在则创建parser
            if user_opt not in sys_opts:
                sys.stderr.write('ERROR: unknown option "%s"\n' % user_opt)
                sys.stderr.write(self.helper)
                sys.exit(1)
            parser = ArgumentParser(
                prog=Conf.prog,
                usage=f'\n  {Conf.usage}',
                description=Conf.description,
            )
            parser.add_argument('command')
            parser.add_argument('option')
            sys_opt = self.options[sys_opts.index(user_opt)]
            for a, r, h in sys_opt.args:
                if r == -1:
                    parser.add_argument(a)
                else:
                    parser.add_argument(f'--{a}', f'-{a[0]}', required=r, help=h)
            self.parse_args = parser.parse_args()
            return sys_opt.callcmd
        else:
            if self.options.args:
                parser = ArgumentParser(
                    prog=Conf.prog,
                    usage=f'\n  {Conf.usage}',
                    description=Conf.description,
                )
                parser.add_argument('command')
                for a, r, h in self.options.args:
                    if r == -1:
                        parser.add_argument(a)
                    else:
                        parser.add_argument(f'--{a}', f'-{a[0]}', required=r, help=h)
                self.parse_args = parser.parse_args()
            return self.options.callcmd

    def help(self):
        if isinstance(self.options, list):
            help_docs = 'Options:\n  '
            help_docs += ', '.join([item.name for item in self.options])
            help_docs += '\n'
            self.helper += help_docs

    def execute(self):
        self.load_callcmd()
        sys.exit()

    def run_cmd(self, argv, helper: str = ''):
        self.argv = argv
        self.helper = helper
        self.execute()
