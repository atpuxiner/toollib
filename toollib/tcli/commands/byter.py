"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:32
@abstract
@description
@history
"""

pip_conf = b'[global]\ntimeout=6000\nindex-url=https://pypi.tuna.tsinghua.edu.cn/simple/\nextra-index-url=\n\thttps://mirrors.aliyun.com/pypi/simple/\n\thttps://mirrors.bfsu.edu.cn/pypi/web/simple/\n\thttps://pypi.doubanio.com/simple/\n\thttps://pypi.python.org/simple/\n\n[install]\ntrusted-host=\n\tpypi.tuna.tsinghua.edu.cn\n\tmirrors.aliyun.com\n\tmirrors.bfsu.edu.cn\n\tpypi.doubanio.com'
conda_conf = b'channels:\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/\n  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/\n  - defaults\nshow_channel_urls: true\n'
