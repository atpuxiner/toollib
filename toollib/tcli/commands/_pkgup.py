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
                Arg("--skips", default="", type=str, help='跳过（默认空，多个用`,`隔开）'),
                Arg("--sep", default="==", choices=["==", ">=", "<=", "~="], help='分隔符（默认==）'),
                Arg("--overwrite", action='store_true', help='是否覆盖（默认不覆盖）'),
            ]}
        )
        return options

    def pkgup(self):
        requirements = self.parse_args.requirements
        if not os.path.isfile(requirements):
            sys.stderr.write(f"ERROR: {requirements} 不存在\n")
            sys.exit(1)
        skips = [s.strip() for s in skips.split(",")] if (skips := self.parse_args.skips) else []
        with open(requirements, "r", encoding="utf-8") as f:
            try:
                pkgs = {}
                for i, t in enumerate(f):
                    if t := t.strip():
                        if t.startswith("#"):
                            continue
                        if pkg := re.split(r"[<>=~]", t, maxsplit=1)[0]:
                            if "#" in t:
                                pkg = t[:t.index("#")]
                            if pkg := pkg.strip():
                                if skips and pkg in skips:
                                    continue
                                pkgs[i] = pkg
                if not pkgs:
                    sys.stdout.write(f"TIP: No matching package\n")
                    sys.exit()
                if pip_pkgs := [p for p in pkgs.values() if p not in ["toollib", "pytcli"]]:
                    subprocess.run(["pip", "install", "-U", *pip_pkgs], check=True)
                new_text = ""
                f.seek(0)
                for i, t in enumerate(f):
                    if pkg := pkgs.get(i):
                        if pkg in ["toollib", "pytcli"]:
                            sys.stdout.write(f"TIP: Please update manually `{pkg}`\n")
                            t = f"{pkg}  # Please update manually"
                        else:
                            pkg_extra = t[t.index(";"):] if ";" in t else ""
                            try:
                                if "[" in pkg and "]" in pkg:
                                    ver = metadata.version(pkg[:pkg.index("[")])
                                else:
                                    ver = metadata.version(pkg)
                                t = f"{pkg}{self.parse_args.sep}{ver}{pkg_extra}"
                            except metadata.PackageNotFoundError:
                                pass
                    if t := t.strip():
                        new_text += f"{t}\n"
                if self.parse_args.overwrite:
                    with open(requirements, "w", encoding="utf-8") as f:
                        f.write(new_text)
                else:
                    with open(requirements + ".up", "w", encoding="utf-8") as f:
                        f.write(new_text)
            except Exception:
                sys.exit(1)
