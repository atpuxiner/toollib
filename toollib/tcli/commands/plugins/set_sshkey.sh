#!/bin/bash
:<<EOF
@author axiner
@version v1.0.0
@created 2023/4/19 11:52
@abstract 设置ssh免密
@description
@history
EOF

function set_pkg_manager() {
  if [[ "$(uname)" == "Linux" ]]; then
    if [[ -n "$(command -v apt-get)" ]]; then
      pkg_manager="apt-get"
    elif [[ -n "$(command -v yum)" ]]; then
      pkg_manager="yum"
    else
      echo -e "apt-get|yum: \033[31m包管理器无法识别\033[0m"
      exit 1
    fi
  else
    echo -e "System only supported: \033[31mLinux\033[0m"
    exit 1
  fi
}

function install_pkgs() {
  pkg_array=($1)
  failed_pkgs=()
  for pkg_string in "${pkg_array[@]}"
  do
    IFS=':' read -ra item <<< "$pkg_string"
    pkg=${item[1]}
    if [[ -z "$(command -v "${item[0]}")" ]]; then
      if ! "$pkg_manager" install -y "$pkg"; then
        echo "Failed to install $pkg"
        failed_pkgs+=("$pkg")
      fi
    fi
  done
  if [ ${#failed_pkgs[@]} -gt 0 ]; then
    echo "Trying to install failed packages: ${failed_pkgs[@]}"
    "$pkg_manager" update
    for pkg in "${failed_pkgs[@]}"; do
      if ! "$pkg_manager" install -y "$pkg"; then
        echo "Failed to install $pkg"
        exit 1
      fi
    done
  fi
}

function gen_key() {
  if ! [ -f "$HOME/.ssh/id_rsa.pub" ]; then
    ssh-keygen -t rsa -P '' -f $HOME/.ssh/id_rsa <<< y
  fi
}

function distribute_key {
  IFS=',' read -ra INFO <<< "$1"
  if [ "${#INFO[@]}" -ne 4 ]; then
    echo -e ""$1"：\033[31mFailed（请检查配置是否正确）\033[0m"
  else
    IP=${INFO[0]}
    USER=${INFO[1]}
    PASS=${INFO[2]}
    PORT=${INFO[3]}
    # set key
    echo -e "\x1dclose\x0d" |timeout 2 telnet "$IP" "$PORT" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo -e "\x1dclose\x0d" |timeout 5 telnet "$IP" "$PORT" > /dev/null 2>&1
    fi
    if [ $? -eq 0 ]; then
      sshpass -p "$PASS" ssh-copy-id -o StrictHostKeyChecking=no -p "$PORT" "$USER@$IP" &>/dev/null
      if [ $? -eq 0 ]; then
        echo -e "$USER@$IP：\033[32mSucceeded\033[0m"
      else
        echo -e "$USER@$IP：\033[31mFailed（请检查配置是否正确）\033[0m"
      fi
    else
      echo -e "$USER@$IP：\033[31mFailed（请检查连接是否畅通）\033[0m"
    fi
  fi
}


pkgs="telnet:telnet sshpass:sshpass timeout:coreutils"
set_pkg_manager
install_pkgs "$pkgs"
gen_key
# Check is a file or a string
if [[ -f $1 ]]; then
  # file
  while read line; do
    distribute_key "$line"
  done < "$1"
else
  # string
  for line in $1; do
    distribute_key "$line"
  done
fi
