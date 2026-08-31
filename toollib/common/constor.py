"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:32
@abstract
@description
@history
"""

conda_conf = b'channels:\n  - defaults\nshow_channel_urls: true\ndefault_channels:\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2\ncustom_channels:\n  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  menpo: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  fastai: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\n  Paddle: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud\nremote_max_retries: 5\nremote_backoff_factor: 2\n'
pyd_setup = b'import sys\nfrom distutils.core import setup, Extension\nfrom Cython.Build import cythonize\nsetup(ext_modules=cythonize(Extension(sys.argv.pop(), sources=[sys.argv.pop()]), language_level="3"))'
docker_daemon = {
    "registry-mirrors": [
        "https://docker.xuanyuan.me",
        "https://docker.1ms.run",
        "https://docker.m.daocloud.io",
        "https://docker.1panel.live",
        "https://docker.nju.edu.cn",
        "https://docker.mirrors.sjtug.sjtu.edu.cn",
        "https://dockerproxy.com",
        "https://mirror.ccs.tencentyun.com"
    ],
    "dns": ["8.8.8.8", "8.8.4.4", "223.5.5.5", "223.6.6.6"]
}
