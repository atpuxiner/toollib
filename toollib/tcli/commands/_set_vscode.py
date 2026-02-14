"""
@author axiner
@version v1.0.0
@created 2026/2/14 14:30
@abstract
@description
@history
"""
from toollib.tcli.base import BaseCmd
from toollib.tcli.commands.plugins.set_vscode import SetVSCode
from toollib.tcli.option import Options


class Cmd(BaseCmd):

    def add_options(self):
        options = Options(
            name='set-vscode',
            desc='设置vscode',
            optional={self.set_vscode: None}
        )
        return options

    def set_vscode(self):
        setter = SetVSCode()
        setter.run()
