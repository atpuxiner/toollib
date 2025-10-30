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
                Arg("-r", "--requirements", default="requirements.txt", type=str,
                    help='依赖文件(默认requirements.txt)'),
                Arg("--overwrite", action='store_true', help='是否覆盖（默认不覆盖）')
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
                pkgs = []
                for t in f:
                    if t := t.strip():
                        if t.startswith("#"):
                            continue
                        if pkg := re.split(r"[<>=~]", t, maxsplit=1)[0].strip():
                            pkgs.append(pkg)
                if not pkgs:
                    sys.stdout.write(f"TIP: {requirements} 未检测到依赖包\n")
                    sys.exit()
                subprocess.run(["pip", "install", "-U",
                                *[p for p in pkgs if p not in ["toollib", "pytcli"]]], check=True)
                with open(requirements, "r", encoding="utf-8") as f:
                    text = f.read()
                for pkg in pkgs:
                    repl = pkg
                    if pkg in ["toollib", "pytcli"]:
                        sys.stdout.write(f"TIP: 请手动更新`{pkg}`\n")
                    else:
                        try:
                            ver = metadata.version(pkg)
                            repl = f"{pkg}=={ver}"
                        except metadata.PackageNotFoundError:
                            pass
                    text = re.sub(
                        pattern=rf"^\s*{re.escape(pkg)}(?:\s*$|\s*(?:==|~=|>=|<=|!=|<|>).*)",
                        repl=repl,
                        string=text,
                        flags=re.MULTILINE,
                    )
                if self.parse_args.overwrite:
                    with open(requirements, "w", encoding="utf-8") as f:
                        f.write(text)
                else:
                    with open(requirements + ".up", "w", encoding="utf-8") as f:
                        f.write(text)
            except Exception:
                sys.exit(1)
