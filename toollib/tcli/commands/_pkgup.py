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
from toollib.tcli.option import Arg, Options

try:
    from packaging.markers import Marker
except ImportError:
    try:
        from pip._vendor.packaging.markers import Marker
    except ImportError:
        Marker = None


class Cmd(BaseCmd):
    # 自身包（避免运行过程中自我升级）
    self_pkgs = ("toollib", "pytcli")
    # PEP 508: 名称 + extras + 版本约束
    req_re = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^]]*])?\s*(.*)$")

    def add_options(self):
        options = Options(
            name="pkgup",
            desc="包更新",
            optional={
                self.pkgup: [
                    Arg(
                        "-r",
                        "--requirements",
                        default="requirements.txt",
                        type=str,
                        help="依赖文件（默认requirements.txt）",
                    ),
                    Arg("--skips", default="", type=str, help="跳过（默认空，多个用`,`隔开）"),
                    Arg(
                        "--sep",
                        default="keep",
                        choices=["keep", ">=", "<=", "~=", "=="],
                        help="分隔符（默认keep，keep则保留原运算符）",
                    ),
                    Arg("--overwrite", action="store_true", help="是否覆盖"),
                ]
            },
        )
        return options

    def pkgup(self):
        requirements = self.parse_args.requirements
        if not os.path.isfile(requirements):
            sys.stderr.write(f"ERROR: {requirements} 不存在\n")
            sys.exit(1)
        skips = {self.norm_name(s) for s in (self.parse_args.skips or "").split(",") if s.strip()}
        try:
            with open(requirements, "r", encoding="utf-8") as f:
                entries = self.logical_lines(f)
            pkgs = {}
            for i, (_, text) in enumerate(entries):
                if req := self.parse_req(text):
                    name, _, _, marker, _ = req
                    if self.norm_name(name) in skips:
                        continue
                    # 标记不匹配当前环境，不能拿本机版本去覆盖别的环境
                    if not self.marker_matched(marker):
                        sys.stdout.write(f"TIP: Marker not matched `{name}`\n")
                        continue
                    pkgs[i] = req
            if not pkgs:
                sys.stdout.write("TIP: No matching package\n")
                sys.exit()
            pip_pkgs = dict.fromkeys(
                f"{n}{e}" for n, e, *_ in pkgs.values() if self.norm_name(n) not in self.self_pkgs
            )
            if pip_pkgs and subprocess.run(["pip", "install", "-U", *pip_pkgs]).returncode != 0:
                sys.stderr.write("WARN: pip install 未全部成功，未装上的包将回填原内容\n")
            new_lines = []
            for i, (raws, _) in enumerate(entries):
                if req := pkgs.get(i):
                    name, extras, spec, marker, comment = req
                    if self.norm_name(name) in self.self_pkgs:
                        sys.stdout.write(f"TIP: Please update manually `{name}`\n")
                    elif ver := self.pkg_version(name):
                        new_lines.append(f"{name}{extras}{self.pick_sep(spec, name)}{ver}{marker}{comment}")
                        continue
                    else:
                        sys.stdout.write(f"TIP: Not installed `{name}`\n")
                new_lines.extend(raws)
            dst = requirements if self.parse_args.overwrite else requirements + ".up"
            with open(dst, "w", encoding="utf-8") as f:
                f.write("\n".join(t.rstrip() for t in new_lines) + "\n")
            sys.stdout.write(f"TIP: Written to `{dst}`\n")
        except Exception as e:
            sys.stderr.write(f"ERROR: {e}\n")
            sys.exit(1)

    @staticmethod
    def norm_name(name: str) -> str:
        """PEP 503 名称归一化"""
        return re.sub(r"[-_.]+", "-", name.strip()).lower()

    def pick_sep(self, spec: str, name: str) -> str:
        """--sep为keep时沿用原运算符；`< > !=`及多段约束会把新版本排除在外，退回`==`"""
        if (sep := self.parse_args.sep) != "keep":
            return sep
        if m := re.fullmatch(r"(===|==|>=|<=|~=)\s*[^,;\s]+", spec):
            return m.group(1)
        if spec:
            sys.stdout.write(f"TIP: Cannot keep `{spec}`, use `==` for `{name}`\n")
        return "=="

    @staticmethod
    def marker_matched(marker: str) -> bool:
        """环境标记是否匹配当前环境（无标记视为匹配；无法判定时视为不匹配，保留原内容）"""
        if not (marker := marker.strip().lstrip(";").strip()):
            return True
        if Marker is None:
            return False
        try:
            return bool(Marker(marker).evaluate())
        except Exception:
            return False

    @staticmethod
    def pkg_version(name: str):
        for n in (name, name.replace("-", "_"), name.replace("_", "-")):
            try:
                return metadata.version(n)
            except metadata.PackageNotFoundError:
                continue
        return None

    @staticmethod
    def logical_lines(f) -> list:
        """合并反斜杠续行，返回[(原始行列表, 逻辑内容), ...]"""
        entries, raws, buf = [], [], []
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            raws.append(line)
            if (stripped := line.rstrip()).endswith("\\"):
                buf.append(stripped[:-1].strip())
                continue
            buf.append(line.strip())
            entries.append((raws, " ".join(t for t in buf if t)))
            raws, buf = [], []
        if raws:
            entries.append((raws, " ".join(t for t in buf if t)))
        return entries

    @classmethod
    def parse_req(cls, line: str):
        """解析为(名称, extras, 版本约束, 环境标记, 行尾注释)；非普通依赖行返回None（原样保留）"""
        if not (body := line.strip()) or body.startswith("#"):
            return None
        # 行尾注释（`#`前须有空白，避免误伤`#egg=`/`#subdirectory=`）
        parts = re.split(r"\s+#", body, maxsplit=1)
        body = parts[0].strip()
        comment = f"  # {parts[1].strip()}" if len(parts) == 2 else ""
        # pip选项行：-r/-e/-i/--index-url/--no-binary/--hash等
        if body.startswith("-"):
            return None
        # 环境标记
        body, _, marker = body.partition(";")
        body, marker = body.strip(), marker.strip()
        marker = f"; {marker}" if marker else ""
        # VCS/远程URL/本地路径/直接引用
        if "://" in body or "@" in body or body.startswith((".", "/", "~")):
            return None
        if re.match(r"^[a-zA-Z]:[\\/]|^\w+\+", body):
            return None
        if not (m := cls.req_re.match(body)):
            return None
        name, extras, spec = m.group(1), m.group(2) or "", m.group(3).strip()
        # 版本约束无法识别，或后面还跟着pip选项（如`torch>=2.1.0 --only-binary xx`）
        if spec and (not re.match(r"[<>=!~]", spec) or re.search(r"\s-", spec)):
            return None
        return name, extras, spec, marker, comment
