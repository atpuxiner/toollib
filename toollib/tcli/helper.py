"""
@author axiner
@version v1.0.0
@created 2022/6/26 15:51
@abstract
@description
@history
"""
prog = 'pytcli'
description = 'A command line for python toollib package'
usage = """Usage:
  pytcli <command> [options]
Commands:
  -h/--help         帮助
  set-pip           设置pip源
  set-conda         设置conda源
  set-mirrors       设置镜像源
  set-sshkey        设置ssh免密
  docker            docker操作
  py2pyd            py转pyd
"""

set_pip = """usage:
  pytcli set-pip
options:
  -h/--help     帮助
"""

set_conda = """usage:
  pytcli set-conda
options:
  -h/--help     帮助
"""

set_mirrors = """usage:
  pytcli set-mirrors
options:
  -h/--help     帮助
  -s/--sysname  系统名称（包括版本号）
"""

set_sshkey = """usage:
  pytcli set-sshkey
options:
  -h/--help     帮助
  -i/--infos    主机信息（"ip1,user1,pass1,port1 ip2,user2,pass2,port2 ..."|也可指定文件:一行一个） 
  --sysname     系统名称（以防自动获取不精确）
"""

docker = """usage:
  pytcli docker [options]
options:
  -h/--help     帮助
  install       安装
    --sysname   系统名称（以防自动获取不精确）
  set-daemon    设置daemon配置（镜像源等）
    --sysname   系统名称（以防自动获取不精确）
  toyml         yml写入（服务配置）
    -n/--name       服务名称（多个用逗号隔开）
    -o/--outdir     输出目录
    -f/--filename   文件名称
"""

py2pyd = """usage:
  pytcli py2pyd [options]
options:
  -h/--help         帮助
  -s/--src          源（py目录或文件）
  -p/--postfix      后缀（默认为Pyd）
  -e/--exclude      排除编译（适用正则，使用管道等注意加引号）
  -i/--ignore       忽略复制（多个逗号隔开）
  -c/--clean        清理临时
"""
