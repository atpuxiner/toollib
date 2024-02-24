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
  snowflake         雪花服务    
  bash              bash模板
  grpc              grpc模板
"""

set_pip = """usage:
  pytcli set-pip
options:
  -h/--help     帮助
  -s/--src      源（tsinghua|aliyun|bfsu|douban|pypi）[可选]
  -t/--timeout  超时[可选]
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
  --sysname     系统名称（以防自动获取不精确）[可选]
"""

docker = """usage:
  pytcli docker [options]
options:
  -h/--help     帮助
  install       安装
    --sysname   系统名称（以防自动获取不精确）[可选]
  set-daemon    设置daemon配置（镜像源等）
    --sysname   系统名称（以防自动获取不精确）[可选]
  toyml         yml写入（服务配置）
    -n/--name       服务名称（多个用逗号隔开）
    -o/--outdir     输出目录[可选]
    -f/--filename   文件名称[可选]
"""

py2pyd = """usage:
  pytcli py2pyd [options]
options:
  -h/--help         帮助
  -s/--src          源（py目录或文件）
  -p/--postfix      后缀（默认为Pyd）[可选]
  -e/--exclude      排除编译（适用正则，使用管道等注意加引号）[可选]
  -i/--ignore       忽略复制（多个逗号隔开）[可选]
  -c/--clean        清理临时[可选]
"""

snowflake = """usage:
  pytcli snowflake [options]
options:
  -h/--help         帮助
  --host            host[可选]
  --port            port[可选]
  --workers         进程数[可选]
"""

bash = """usage:
  pytcli bash [options]
options:
  -h/--help     帮助
  -f/--file     文件
  -c/--cmds     命令（多个用`,`隔开，且不能包含空格）
  -o/--opts     选项（多个用`,`隔开，且不能包含空格，短选项单字符，长选项多字符，后可接`:`表示需要值，如：s/src:,d/dest:）[可选]
"""

grpc = """usage:
  pytcli grpc [options]
options:
  -h/--help     帮助
  -n/--name     名称[可选]
  -d/--dir      目录[可选]
"""
