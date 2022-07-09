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
  docker            docker安装等
  set-conda         设置conda国内源
  set-pip           设置pip国内源
  set-source        重新加载.bashrc等配置
  set-sshkey        设置ssh免密登录(可批量设置)
  set-yum           设置yum阿里源
  sync              远程同步文件
"""

docker = """usage:
  pytcli docker [options]
options:
  -h/--help     帮助
  install       安装
  start         启动
    -n/--name   镜像名称
"""

set_conda = """usage:
  pytcli set-conda
options:
  -h/--help     帮助
"""

set_pip = """usage:
  pytcli set-pip
options:
  -h/--help     帮助
"""

set_source = """usage:
  pytcli set-source
options:
  -h/--help     帮助
"""

set_sshkey = """usage:
  pytcli set-sshkey
options:
  -h/--help     帮助
"""

set_yum = """usage:
  pytcli set-yum
options:
  -h/--help     帮助
"""

sync = """usage:
  pytcli sync
options:
  -h/--help     帮助
  -s/--src      源目录
  -d/--dest     目标目录
  -i/--ip       目标ip
  -u/--user     目标用户[需免密登录]
"""
