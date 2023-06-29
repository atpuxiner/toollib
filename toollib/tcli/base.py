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
    usage: str
    options: Options
    curr_usage: str
    curr_option: str
    parse_args: Namespace

    def add_options(self) -> Options:
        raise NotImplementedError('subclasses of BaseCmd must provide a add_options() method')

    def load_options(self):
        options = self.add_options()
        if not isinstance(options, Options):
            raise TypeError('add_options() return type only supported: Options')
        return options

    def set_init(self, argv, usage):
        self.argv = argv
        self.usage = usage
        self.options = self.load_options()
        self.curr_usage = getattr(helper, self.argv[0], helper.usage)
        self.curr_option = self.argv[1] if self.argv[1:] else None
        if self.curr_option and self.curr_option in ['-h', '--help']:
            sys.stdout.write(self.curr_usage)
            sys.exit()

    @property
    def load_callcmd(self) -> t.Callable:
        subcmds = self.options.subcmds
        posargs = ['command']
        # check
        if len(subcmds) > 1:
            if not self.curr_option:
                sys.stderr.write('ERROR: Option is required\n')
                sys.stderr.write(self.curr_usage)
                sys.exit(1)
            curr_optional = subcmds.get(self.curr_option.replace('-', '_'))
            if not curr_optional:
                sys.stderr.write("ERROR: Unknown option '%s'\n" % self.curr_option)
                sys.stderr.write(self.curr_usage)
                sys.exit(1)
            posargs.append('option')
        else:
            _, curr_optional = subcmds.popitem()
        # add args
        curr_subcmd, curr_args = curr_optional
        parser = ArgumentParser(
            add_help=False,
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

    def run(self, argv, usage: str):
        self.set_init(argv, usage)
        self.load_callcmd()
        sys.exit()
