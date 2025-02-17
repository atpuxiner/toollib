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
            name='repkgs',
            desc='刷新包',
            optional={self.repkgs: [
                Arg("-r", "--requirements", required=True, type=str, help='依赖文件'),
                Arg("-o", "--overwrite", action='store_true', help='是否覆盖（默认不覆盖）')
            ]}
        )
        return options

    def repkgs(self):
        requirements = self.parse_args.requirements
        if not os.path.isfile(requirements):
            sys.stderr.write(f"ERROR: {requirements} 不存在\n")
            sys.exit(1)
        with open(requirements, "r", encoding="utf-8") as f:
            try:
                pkgs = [re.split(r"[><~=]", l, maxsplit=1)[0].strip()
                        for l in f if not l.startswith("#") and l.strip()]
                subprocess.run(["pip", "install", "-U", *pkgs], check=True)
                with open(requirements, "r", encoding="utf-8") as f:
                    text = f.read()
                for pkg in pkgs:
                    try:
                        ver = metadata.version(pkg)
                        repl = f"{pkg}=={ver}"
                    except metadata.PackageNotFoundError:
                        repl = f"{pkg}"
                    text = re.sub(rf"^{pkg}[^\n]*", repl, text, flags=re.MULTILINE)
                if self.parse_args.overwrite:
                    with open(requirements, "w", encoding="utf-8") as f:
                        f.write(text)
                else:
                    with open(requirements + ".refresh", "w+", encoding="utf-8") as f:
                        f.write(text)
            except Exception:
                sys.exit(1)
