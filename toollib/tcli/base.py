"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""
import os
import sys
from argparse import ArgumentParser, Namespace

import typing as t

from toollib.tcli import helper
from toollib.tcli.option import Options


class BaseCmd:

    argv: list
    options: Options
    parse_args: Namespace
    usage: str
    curr_usage: str

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
        # check
        curr_cmd = self.argv[0]
        self.curr_usage = getattr(helper, curr_cmd, helper.usage)
        subcmds = self.options.subcmds
        posargs = ['command']
        curr_option = self.argv[1] if self.argv[1:] else None
        if len(subcmds) > 1:
            self._check_option(curr_option, mode=1)
            posargs.append('option')
        else:
            if curr_option:
                self._check_option(curr_option, mode=2)
            curr_option = curr_cmd
        curr_optional = subcmds.get(curr_option.replace('-', '_'))
        if not curr_optional:
            self._check_option(curr_option, mode=3)
        # add args
        curr_subcmd, curr_args = curr_optional
        parser = ArgumentParser(
            prog=f'[{helper.prog}]',
            usage=self.curr_usage.replace('usage:', ''),
            description=helper.description,
        )
        _ = [parser.add_argument(pos) for pos in posargs]
        if curr_args:
            for arg in curr_args:
                name_or_flags, kwargs = arg.parse_arg
                parser.add_argument(*name_or_flags, **kwargs)
        self.parse_args = parser.parse_args(self.argv)
        if hasattr(self.parse_args, 'sysname'):
            if self.parse_args.sysname and self.parse_args.sysname != "''":
                os.environ.setdefault('sysname', self.parse_args.sysname)
        return curr_subcmd

    def _check_option(self, option, mode):
        if mode == 1:
            if not option:
                sys.stderr.write('ERROR: Option is required\n')
                sys.stderr.write(self.curr_usage)
                sys.exit(1)
        else:
            if option in ['-h', '--help']:
                sys.stdout.write(self.curr_usage)
                sys.exit()
            if mode == 3:
                sys.stderr.write('ERROR: Unknown option "%s"\n' % option)
                sys.stderr.write(self.curr_usage)
                sys.exit(1)

    def execute(self):
        self.load_callcmd()
        sys.exit()

    def runcmd(self, argv, usage: str):
        self.argv = argv
        self.usage = usage
        self.execute()
