"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:20
@abstract
@description
@history
"""
import importlib
import sys

from toollib import here
from toollib.tcli import Conf


class Cmd:

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[1:]
        self.commands = self.find_commands()
        self.helper = self.help()
        if not self.argv:
            sys.stdout.write(self.help())
            sys.exit()
        currcmd = self.argv[0]
        if currcmd not in self.commands:
            sys.stderr.write('ERROR: unknown command "%s"\n' % currcmd)
            sys.stderr.write(self.helper)
            sys.exit(1)
        self.currcmd = currcmd

    def help(self):
        help_docs = f'Usage:\n  {Conf.usage}\n' \
                    'Commands:\n  '
        help_docs += ', '.join(self.commands)
        help_docs += '\n'
        return help_docs

    @staticmethod
    def find_commands():
        commands_dir = here.joinpath('tcli/commands')
        commands = [cmd.stem[1:] for cmd in commands_dir.rglob('_*.py') if cmd.stem != '__init__']
        return commands

    def load_command_class(self):
        cmdmod = importlib.import_module('toollib.tcli.commands._%s' % self.currcmd)
        return cmdmod.Cmd()

    def execute(self):
        cmdcls = self.load_command_class()
        cmdcls.run_cmd(self.argv, self.helper)


def run(argv=None):
    cmd = Cmd(argv)
    cmd.execute()
