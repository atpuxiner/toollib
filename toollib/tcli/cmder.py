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
from pathlib import Path

from toollib import here
from toollib.tcli import Conf


class Cmd:

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.commands = self.find_commands()
        self.helper = self.help()
        if not self.argv[1:]:
            sys.stdout.write(self.help())
            sys.exit()
        if self.argv[1] not in self.commands:
            sys.stderr.write('ERROR: unknown command "%s"\n' % self.argv[1])
            sys.stderr.write(self.helper)
            sys.exit(1)

        self.prog_name = Path(self.argv[1]).stem

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

    def load_command_class(self, prog_name):
        """
        Given a command name, return the Command class instance.
        """
        module = importlib.import_module('toollib.tcli.commands._%s' % prog_name)
        return module.Cmd()

    def execute(self):
        module = self.load_command_class(self.prog_name)
        module.run_cmd(self.argv, self.helper)


def run(argv=None):
    cmd = Cmd(argv)
    cmd.execute()
