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

    def parse_posargs_default(self) -> t.Tuple[dict, dict]:
        args = self.argv[1:]
        posargs, optargs = {}, {}
        index = 0
        while args:
            if args[0] == '-' or args[0] == '--':
                args = args[1:]
            if args[0].startswith('-') or args[0].startswith('--'):
                optargs.setdefault(args[0].lstrip('-')[0], index)
                args = args[2:]
                index += 1
            else:
                posargs.setdefault(args[0], index)
                args = args[1:]
            index += 1
        return posargs, optargs

    @property
    def load_callcmd(self) -> t.Callable:
        self.load_options()
        self.help()
        parser_flag, parser = False, None
        sys_posopts_default = []
        if isinstance(self.options, list):
            parser_flag = True
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
            _index = 0
            for item in sys_opt.args:
                key = item.get('key')
                required = item.get('required')
                help = item.get('help')
                if required == -1:
                    parser.add_argument(key)
                    default_by = item.get('default_by')
                    if default_by:
                        sys_posopts_default.append((default_by, _index))
                else:
                    parser.add_argument(f'--{key}', f'-{key[0]}', required=required, help=help)
                _index += 1
            callcmd = sys_opt.callcmd
        else:
            if self.options.args:
                parser_flag = True
                parser = ArgumentParser(
                    prog=Conf.prog,
                    usage=f'\n  {Conf.usage}',
                    description=Conf.description,
                )
                parser.add_argument('command')
                _index = 0
                for item in self.options.args:
                    key = item.get('key')
                    required = item.get('required')
                    help = item.get('help')
                    if required == -1:
                        parser.add_argument(key)
                        default_by = item.get('default_by')
                        if default_by:
                            sys_posopts_default.append((default_by, _index))
                    else:
                        parser.add_argument(f'--{key}', f'-{key[0]}', required=required, help=help)
            callcmd = self.options.callcmd
        if parser_flag is True:
            posargs, optargs = self.parse_posargs_default()
            for _default_by, _index in sys_posopts_default:
                if _default_by[0] in optargs:
                    if len(posargs) == _index + 1:  # cmd map，so +1
                        self.argv.insert(_index + 2, False)  # and file，so +2
            self.parse_args = parser.parse_args(self.argv[1:])
        else:
            self.parse_args = Namespace()
        return callcmd

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
