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
                Arg("-r", "--requirements", default="requirements.txt", type=str, help='依赖文件(默认requirements.txt)'),
                Arg("--rewrite", action='store_true', help='是否重写（默认不重写）')
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
                pkgs = [re.split(r"[<>=~]", l, maxsplit=1)[0].strip()
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
                if self.parse_args.rewrite:
                    with open(requirements, "w", encoding="utf-8") as f:
                        f.write(text)
                else:
                    with open(requirements + ".up", "w", encoding="utf-8") as f:
                        f.write(text)
            except Exception:
                sys.exit(1)
