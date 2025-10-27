import re
import shutil
from pathlib import Path
from typing import Callable


def copytree(
        src: str | Path,
        dst: str | Path,
        ignore_regex: str | None = None,
        dirs_exist_ok: bool = False,
        copy_function: Callable[[str, str], None] = shutil.copy2,
):
    """
    复制目录树

    e.g.::

        copytree(src=r"D:/myproj", dst=r"D:/myproj-bak", ignore_regex=r"^logs($|/)")

    :param src: 源目录路径
    :param dst: 目标目录路径
    :param ignore_regex: 忽略正则表达式（使用'/'作为路径分隔符）
    :param dirs_exist_ok: 是否允许目标目录已存在
    :param copy_function: 文件复制函数（默认 shutil.copy2）
    """
    src_path = Path(src)
    dst_path = Path(dst)
    if not src_path.exists() or not src_path.is_dir():
        raise ValueError(f"Directory not found: {src_path}")
    ignore_pattern = re.compile(ignore_regex) if ignore_regex else None
    dst_path.mkdir(parents=True, exist_ok=dirs_exist_ok)

    def should_ignore(rel_path_str: str) -> bool:
        """判断相对路径是否应被忽略"""
        if not ignore_pattern:
            return False
        normalized = rel_path_str.replace("\\", "/")
        return bool(ignore_pattern.match(normalized))

    def walk_and_copy(current_src: Path, current_dst: Path):
        """递归遍历并复制文件和子目录"""
        dirs = []
        files = []
        for entry in current_src.iterdir():
            rel_path = entry.relative_to(src_path)
            rel_path_str = str(rel_path).replace("\\", "/")
            if should_ignore(rel_path_str):
                continue
            if entry.is_dir():
                dirs.append((entry, rel_path_str))
            elif entry.is_file():
                files.append((entry, rel_path_str))
        current_dst.mkdir(exist_ok=True)
        for src_file, rel_file_str in files:
            dst_file = dst_path / rel_file_str
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            copy_function(str(src_file), str(dst_file))
        for src_dir, rel_dir_str in dirs:
            next_dst = dst_path / rel_dir_str
            walk_and_copy(src_dir, next_dst)

    walk_and_copy(src_path, dst_path)
