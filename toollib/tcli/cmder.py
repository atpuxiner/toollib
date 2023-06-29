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
from toollib.tcli import helper


class Cmd:

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[1:]
        self.commands = self.find_commands()
        self.usage = helper.usage
        if not self.argv:
            sys.stdout.write(self.usage)
            sys.exit()
        curr_command = self.argv[0]
        self._check_command(curr_command)
        self.argv[0] = curr_command.replace('-', '_')

    def _check_command(self, command):
        if command not in self.commands:
            if command in ['-h', '--help']:
                sys.stdout.write(self.usage)
                sys.exit()
            sys.stderr.write("ERROR: Unknown command '%s'\n" % command)
            sys.stderr.write(self.usage)
            sys.exit(1)

    @staticmethod
    def find_commands():
        commands_dir = here.joinpath('tcli/commands')
        commands = [cmd.stem[1:].replace('_', '-') for cmd in commands_dir.rglob('_*.py')
                    if cmd.stem != '__init__']
        return commands

    def load_command_class(self):
        cmdmod = importlib.import_module('toollib.tcli.commands._%s' % self.argv[0])
        return cmdmod.Cmd()

    def execute(self):
        cmdcls = self.load_command_class()
        cmdcls.run(self.argv, self.usage)


def run(argv=None):
    cmd = Cmd(argv)
    cmd.execute()
