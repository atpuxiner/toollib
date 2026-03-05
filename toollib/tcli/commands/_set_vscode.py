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
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):
    def add_options(self):
        options = Options(
            name="set-vscode",
            desc="设置vscode配置",
            optional={
                self.set_vscode: [
                    Arg("--dest", "-d", type=str, default=".", help="目标路径"),
                    Arg("--conda", action="store_true", help="是否初始化conda"),
                    Arg("--prettier", action="store_true", help="是否设置prettier"),
                ]
            },
        )
        return options

    def set_vscode(self):
        dest = self.parse_args.dest
        conda = self.parse_args.conda
        prettier = self.parse_args.prettier
        setter = SetVSCode(
            project_dir=dest,
            enable_conda=conda,
            enable_prettier=prettier,
        )
        setter.run()
