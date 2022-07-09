"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:32
@abstract
@description
@history
"""

pip_conf = b'[global]\ntimeout=6000\nindex-url=https://pypi.tuna.tsinghua.edu.cn/simple/\nextra-index-url=\n\thttp://mirrors.aliyun.com/pypi/simple/\n\thttp://pypi.douban.com/simple/\n\thttp://pypi.mirrors.ustc.edu.cn/simple/\n\thttps://pypi.python.org/simple/\n\n[install]\ntrusted-host=\n\tmirrors.aliyun.com\n\tpypi.douban.com\n\tpypi.mirrors.ustc.edu.cn'
conda_conf = b'channels:\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/\n  - defaults\nshow_channel_urls: true\n'
