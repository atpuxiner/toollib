"""
@author axiner
@version v1.0.0
@created 2023/5/23 14:52
@abstract
@description
@history
"""

BASH_TPL = """#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
WORK_DIR=$(pwd)

VERSION=1.0.0

# 帮助文档
HELP_DOCS=$(cat <<EOF
Usage:
  bash $SCRIPT_NAME <command> [options]
Commands:
  待完善
Options:
  待完善
EOF
)

# 解析参数
SHORT_OPTS="h@SHORT_OPTS"
LONG_OPTS="help,version@LONG_OPTS"
@DEFAULT_FALSE_OPTS
if [[ -z "$1" ]]; then
  echo "$HELP_DOCS"
  exit
fi
PARSED_OPTS=$(getopt -o $SHORT_OPTS -l $LONG_OPTS -- "$@")
if [ $? != 0 ]; then
  exit 1
fi
eval set -- "$PARSED_OPTS"
while true; do
  case $1 in
  -h|--help)
    echo "$HELP_DOCS"
    exit
    ;;
  --version)
    echo "$VERSION"
    exit
    ;;@ALL_OPTS
  --)
    shift
    break
    ;;
  *)
    echo "Invalid argument: $2" >&2
    exit 1
    ;;
  esac
done
# if [[ -z "$XXX" ]]; then
#   echo "Missing argument: XXX must be provided" >&2
#   exit 1
# fi

# 功能函数
@ALL_FUNCS

# 解析命令
case $1 in
@ALL_CMDS
*)
  echo "ERROR: Unknown command '$1'" >&2
  exit 1
  ;;
esac
"""

VAR_PREFIX = 'VAR_'
OPT_DEFAULT = """
  {opt})
    {var}={value}
    shift 2
    ;;"""
FUNC_DEFAULT = """function func_{cmd}() {{
  echo "{cmd}: 待实现"
}}

"""
CMD_DEFAULT = """{cmd})
  func_{cmd}
  ;;
"""
