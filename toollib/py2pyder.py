"""
@author axiner
@version v1.0.0
@created 2023/4/7 15:14
@abstract py转pyd
@description
@history
"""
import os
import re
import shutil
import subprocess
import sys

from toollib.common import constor
from toollib.utils import listfile

try:
    from Cython.Build import cythonize
except ImportError as err:
    sys.stderr.write(f"ERROR: {err}\n")
    sys.exit(1)

__all__ = ['Py2Pyder']


class Py2Pyder:
    """
    py转pyd

    e.g.::

        py2pyder = Py2Pyder(src=r'D:\pyprj', exclude=r'main.py|tests/')
        py2pyder.run()

        - 注：
            - 自动跳过: __init__.py, 空文件，只存在注释的文件，当然还有非py文件
            - 若编译不成功或编译后执行不成功：
                - 确保python代码的正确性与严谨性
                - 编译失败的，Pyd目录下对应的源文件不会删除
                - 编译后的文件执行，需要与编译时的python版本、操作系统一致
                - 实在编译不了或执行不了，可加入exclude用源文件代替
            - exclude: 排除编译（适用正则）
                - 文件夹加正斜杠'/'即可，如：tests/, tests/a/
                - 多个则用'|'隔开，如：main.py|tests/
                - 项目的入口文件一般是不编译的，加入exclude即可
            - 输出：Pyd目录（默认源+Pyd），该目录与src结构一致

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            src: str,
            postfix: str = 'Pyd',
            exclude: str = None,
            ignore: str = '.git,.idea,__pycache__',
            is_clean: bool = False,
    ):
        """
        初始化
        :param src: 源（py目录或文件）
        :param postfix: 后缀（默认为Pyd）
        :param exclude: 排除编译（适用正则）
        :param ignore: 忽略复制（多个逗号隔开）
        :param is_clean: 是否清理（默认不清理）
        """
        self.src = os.path.abspath(src)
        if os.path.isdir(self.src):
            self.src_is_dir = True
            self.dst = self.src + (postfix or 'Pyd')
        elif os.path.isfile(self.src):
            self.src_is_dir = False
            if self.src.endswith('.py'):
                self.dst = os.path.join(
                    os.path.dirname(self.src),
                    os.path.basename(self.src)[:-3] + (postfix or 'Pyd'))
            else:
                sys.stderr.write(f'ERROR: Only supported py, not {src.split(".")[-1]}\n')
                sys.exit(1)
        else:
            sys.stderr.write(f'ERROR: {src} does not exist\n')
            sys.exit(1)
        self.exclude = exclude
        self.ignore = ignore
        self.is_clean = is_clean
        self.setuppy = os.path.join(self.dst, '.setuppy')

    def run(self):
        """
        执行
        :return:
        """
        self._init_setup()
        self._build()

    def _init_setup(self):
        if not os.path.isdir(self.dst):
            os.mkdir(self.dst)
        if self.src_is_dir:
            ignore_cp = shutil.ignore_patterns(*self.ignore.split(',')) if self.ignore else None
            shutil.copytree(self.src, self.dst, ignore=ignore_cp, dirs_exist_ok=True)
        else:
            shutil.copy(self.src, self.dst)
        with open(self.setuppy, 'wb') as fp:
            fp.write(constor.pyd_setup)

    def _build(self):
        os.chdir(self.dst)
        _ = len(self.dst)
        for pyfile in listfile(self.dst, '*.py', is_str=True, is_r=True):
            if pyfile.endswith('__init__.py'):
                print(f'跳过init：{pyfile}')
                continue
            if os.path.getsize(pyfile) == 0:
                print(f'跳过为空：{pyfile}')
                continue
            with open(pyfile, 'r', encoding='utf8') as fp:
                content = re.compile(r'^\s*""".*?"""', re.DOTALL | re.MULTILINE).sub(
                    '', re.compile(r'^\s*#.*$', re.MULTILINE).sub(
                        '', fp.read())).strip()
                if not content:
                    print(f'跳过注释：{pyfile}')
                    continue
            rpyfile = pyfile[_:].lstrip('/')
            if self.exclude and re.search(self.exclude, rpyfile):
                print(f'跳过排除：{pyfile}')
                continue
            print(f'正在处理：{pyfile}')
            result = subprocess.run([
                'python', self.setuppy, 'build_ext', '-i',
                pyfile.replace('/', os.sep),
                rpyfile[:-3].replace('/', '.'),
            ])
            if result.returncode == 0:
                os.remove(pyfile)
            cpyfile = pyfile[:-3] + '.c'
            if os.path.isfile(cpyfile):
                os.remove(cpyfile)
        if self.is_clean:
            subprocess.run(['python', self.setuppy, 'clean', 'xxx', 'xxx'])
            shutil.rmtree(os.path.join(self.dst, 'build'), ignore_errors=True)
        os.remove(self.setuppy)
