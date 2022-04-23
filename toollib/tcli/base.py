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
from toollib.tcli.option import Options


class BaseCmd:

    argv: list
    options: Options
    parse_args: Namespace
    helper: str

    def add_options(self) -> Options:
        raise NotImplementedError('subclasses of BaseCmd must provide a add_options() method')

    def load_options(self):
        options = self.add_options()
        if not isinstance(options, Options):
            raise TypeError('"add_options()" return type only supported: Options')
        self.options = options

    @property
    def load_callcmd(self) -> t.Callable:
        self.load_options()
        self.help()
        # check
        curr_cmd = self.argv[0]
        subcmds = self.options.subcmds
        posargs = ['command']
        if len(subcmds) > 1:
            if not self.argv[1:]:
                sys.stderr.write('ERROR: option is required\n')
                sys.stderr.write(self.helper)
                sys.exit(1)
            curr_option = self.argv[1]
            posargs.append('option')
        else:
            curr_option = curr_cmd
        curr_optional = subcmds.get(curr_option)
        if not curr_optional:
            sys.stderr.write('ERROR: unknown option "%s"\n' % curr_option)
            sys.stderr.write(self.helper)
            sys.exit(1)
        # add args
        curr_subcmd, curr_args = curr_optional
        parser = ArgumentParser(
            prog=Conf.prog,
            usage=f'\n  {Conf.usage}',
            description=Conf.description,
        )
        _ = [parser.add_argument(pos) for pos in posargs]
        if curr_args:
            for arg in curr_args:
                name_or_flags, kwargs = arg.parse_arg
                parser.add_argument(*name_or_flags, **kwargs)
        self.parse_args = parser.parse_args(self.argv)
        return curr_subcmd

    def help(self):
        help_docs = 'Options:\n  '
        help_docs += ', '.join(self.options.subcmds.keys())
        help_docs += '\n'
        self.helper += help_docs

    def execute(self):
        self.load_callcmd()
        sys.exit()

    def run_cmd(self, argv, helper: str = ''):
        self.argv = argv
        self.helper = helper
        self.execute()
