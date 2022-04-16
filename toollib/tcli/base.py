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
            if user_opt not in sys_opts:
                sys.stderr.write('ERROR: unknown option "%s"\n' % user_opt)
                sys.stderr.write(self.helper)
                sys.exit(1)
            sys_opt = self.options[sys_opts.index(user_opt)]
            posargs = ['command', 'option']
        else:
            sys_opt = self.options
            posargs = ['command']
        parser = ArgumentParser(
            prog=Conf.prog,
            usage=f'\n  {Conf.usage}',
            description=Conf.description,
        )
        _ = [parser.add_argument(pos) for pos in posargs]
        for item in sys_opt.args:
            key = item.get('key')
            required = item.get('required')
            nargs = item.get('nargs')
            _help = item.get('help')
            if required == -1:
                parser.add_argument(key, nargs=nargs, help=_help)
            else:
                parser.add_argument(f'--{key}', f'-{key[0]}',
                                    required=required, nargs=nargs, help=_help)
        self.parse_args = parser.parse_args(self.argv[1:])
        return sys_opt.callcmd

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
