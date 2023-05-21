"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:32
@abstract
@description
@history
"""

pip_conf = b'[global]\ntimeout=6000\nindex-url=https://pypi.tuna.tsinghua.edu.cn/simple/\nextra-index-url=\n\thttps://mirrors.aliyun.com/pypi/simple/\n\thttps://mirrors.bfsu.edu.cn/pypi/web/simple/\n\thttps://pypi.doubanio.com/simple/\n\thttps://pypi.python.org/simple/\n[install]\ntrusted-host=\n\tpypi.tuna.tsinghua.edu.cn\n\tmirrors.aliyun.com\n\tmirrors.bfsu.edu.cn\n\tpypi.doubanio.com'
conda_conf = b'channels:\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/pro/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/mro/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/fastai/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/Paddle/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/menpo/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/\n  - defaults\nshow_channel_urls: true'
pyd_setup = b'import sys\nfrom distutils.core import setup, Extension\nfrom Cython.Build import cythonize\nsetup(ext_modules=cythonize(Extension(sys.argv.pop(), sources=[sys.argv.pop()]), language_level="3"))'
docker_daemon = {
    "registry-mirrors": [
        "https://hub-mirror.c.163.com",
        "https://docker.mirrors.ustc.edu.cn",
        "https://registry.docker-cn.com",
    ],
    "dns": ["8.8.8.8", "8.8.4.4", "223.5.5.5", "223.6.6.6"]
}
