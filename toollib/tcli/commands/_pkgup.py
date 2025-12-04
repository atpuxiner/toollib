"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:31
@abstract
@description
@history
"""
import os
import re
import subprocess
import sys
from importlib import metadata

from toollib.tcli.base import BaseCmd
from toollib.tcli.option import Options, Arg


class Cmd(BaseCmd):

    def __init__(self):
        super().__init__()

    def add_options(self):
        options = Options(
            name='pkgup',
            desc='包更新',
            optional={self.pkgup: [
                Arg("-r", "--requirements", default="requirements.txt", type=str, help='依赖文件（默认requirements.txt）'),
                Arg("-s", "--sep", default="==", choices=["==", ">=", "<=", "~="], help='分隔符（默认==）'),
                Arg("--overwrite", action='store_true', help='是否覆盖（默认不覆盖）'),
            ]}
        )
        return options

    def pkgup(self):
        requirements = self.parse_args.requirements
        if not os.path.isfile(requirements):
            sys.stderr.write(f"ERROR: {requirements} 不存在\n")
            sys.exit(1)
        with open(requirements, "r", encoding="utf-8") as f:
            try:
                pkgs = {}
                for i, t in enumerate(f):
                    if t := t.strip():
                        if t.startswith("#"):
                            continue
                        if pkg := re.split(r"[<>=~]", t, maxsplit=1)[0].strip():
                            pkgs[i] = pkg
                if not pkgs:
                    sys.stdout.write(f"TIP: `{requirements}` No packages detected\n")
                    sys.exit()
                subprocess.run(["pip", "install", "-U",
                                *[p for p in pkgs.values() if p not in ["toollib", "pytcli"]]], check=True)
                new_text = ""
                f.seek(0)
                for i, l in enumerate(f):
                    if pkg := pkgs.get(i):
                        if pkg in ["toollib", "pytcli"]:
                            sys.stdout.write(f"TIP: Please update manually `{pkg}`\n")
                            l = f"{pkg}  # Please update manually"
                        else:
                            try:
                                if "[" in pkg and "]" in pkg:
                                    ver = metadata.version(pkg[:pkg.index("[")])
                                else:
                                    ver = metadata.version(pkg)
                                l = f"{pkg}{self.parse_args.sep}{ver}"
                            except metadata.PackageNotFoundError:
                                pass
                    new_text += f"{l.strip()}\n"
                if self.parse_args.overwrite:
                    with open(requirements, "w", encoding="utf-8") as f:
                        f.write(new_text)
                else:
                    with open(requirements + ".up", "w", encoding="utf-8") as f:
                        f.write(new_text)
            except Exception:
                sys.exit(1)
