"""
@author axiner
@version v1.0.0
@created 2023/5/2 15:00
@abstract
@description
    更新记录：
        - 20230502
@history
"""

# ubuntu
ubuntu_1404 = """deb https://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ trusty main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ trusty-security main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ trusty-updates main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ trusty-backports main restricted universe multiverse

## Not recommended
# deb https://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ trusty-proposed main restricted universe multiverse
"""

ubuntu_1604 = """deb https://mirrors.aliyun.com/ubuntu/ xenial main
deb-src https://mirrors.aliyun.com/ubuntu/ xenial main

deb https://mirrors.aliyun.com/ubuntu/ xenial-updates main
deb-src https://mirrors.aliyun.com/ubuntu/ xenial-updates main

deb https://mirrors.aliyun.com/ubuntu/ xenial universe
deb-src https://mirrors.aliyun.com/ubuntu/ xenial universe
deb https://mirrors.aliyun.com/ubuntu/ xenial-updates universe
deb-src https://mirrors.aliyun.com/ubuntu/ xenial-updates universe

deb https://mirrors.aliyun.com/ubuntu/ xenial-security main
deb-src https://mirrors.aliyun.com/ubuntu/ xenial-security main
deb https://mirrors.aliyun.com/ubuntu/ xenial-security universe
deb-src https://mirrors.aliyun.com/ubuntu/ xenial-security universe
"""

ubuntu_1804 = """deb https://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ bionic main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ bionic-security main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ bionic-updates main restricted universe multiverse

# deb https://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ bionic-proposed main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ bionic-backports main restricted universe multiverse
"""

ubuntu_2004 = """deb https://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse

# deb https://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
"""

# debian
debian_7x = """deb https://mirrors.aliyun.com/debian-archive/debian/ wheezy main non-free contrib
deb https://mirrors.aliyun.com/debian-archive/debian/ wheezy-proposed-updates main non-free contrib
deb-src https://mirrors.aliyun.com/debian-archive/debian/ wheezy main non-free contrib
deb-src https://mirrors.aliyun.com/debian-archive/debian/ wheezy-proposed-updates main non-free contrib
"""

debian_8x = """deb https://mirrors.aliyun.com/debian-archive/debian/ jessie main non-free contrib
deb-src https://mirrors.aliyun.com/debian-archive/debian/ jessie main non-free contrib
"""

debian_9x = """deb https://mirrors.aliyun.com/debian-archive/debian stretch main contrib non-free
#deb https://mirrors.aliyun.com/debian-archive/debian stretch-proposed-updates main non-free contrib
deb https://mirrors.aliyun.com/debian-archive/debian stretch-backports main non-free contrib
deb https://mirrors.aliyun.com/debian-archive/debian-security stretch/updates main contrib non-free
deb-src https://mirrors.aliyun.com/debian-archive/debian stretch main contrib non-free
#deb-src https://mirrors.aliyun.com/debian-archive/debian stretch-proposed-updates main contrib non-free
deb-src https://mirrors.aliyun.com/debian-archive/debian stretch-backports main contrib non-free
deb-src https://mirrors.aliyun.com/debian-archive/debian-security stretch/updates main contrib non-free
"""

debian_10x = """deb https://mirrors.aliyun.com/debian/ buster main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ buster main non-free contrib
deb https://mirrors.aliyun.com/debian-security buster/updates main
deb-src https://mirrors.aliyun.com/debian-security buster/updates main
deb https://mirrors.aliyun.com/debian/ buster-updates main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ buster-updates main non-free contrib
deb https://mirrors.aliyun.com/debian/ buster-backports main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ buster-backports main non-free contrib
"""

debian_11x = """deb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ bullseye main non-free contrib
deb https://mirrors.aliyun.com/debian-security/ bullseye-security main
deb-src https://mirrors.aliyun.com/debian-security/ bullseye-security main
deb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib
deb https://mirrors.aliyun.com/debian/ bullseye-backports main non-free contrib
deb-src https://mirrors.aliyun.com/debian/ bullseye-backports main non-free contrib
"""


mirrors_cmds = {
    # ubuntu
    'ubuntu20.04': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=ubuntu_2004),
        'apt-get update',
    ],
    'ubuntu18.04': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=ubuntu_1804),
        'apt-get update',
    ],
    'ubuntu16.04': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=ubuntu_1604),
        'apt-get update',
    ],
    'ubuntu14.04': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=ubuntu_1404),
        'apt-get update',
    ],
    # debian
    'debian11': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=debian_11x),
        'apt-get update',
    ],
    'debian10': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=debian_10x),
        'apt-get update',
    ],
    'debian9': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=debian_9x),
        'apt-get update',
    ],
    'debian8': [
        'cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'echo "{mirror}" > /etc/apt/sources.list'.format(mirror=debian_8x),
        'apt-get update',
    ],
    # centos
    'centos8': [
        'cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo',
        'yum makecache',
    ],
    'centos7': [
        'cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-7.repo',
        'yum makecache',
    ],
    'centos6': [
        'cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak.$(date +%Y%m%d) 2>/dev/null ; true',
        'curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-vault-6.10.repo',
        'yum makecache',
    ]
}
