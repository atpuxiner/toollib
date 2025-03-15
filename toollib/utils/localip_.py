import socket


def localip(dns_servers: list[str] = None) -> str:
    """
    本地ip

    e.g.::

        ip = utils.localip()
        ip = utils.localip(["8.8.4.4", "1.1.1.1"])  # 使用自定义DNS

        +++++[更多详见参数或源码]+++++

    :param dns_servers: dns服务
    :return:
    """
    default_dns = [
        "223.5.5.5",  # 阿里云DNS
        "180.76.76.76",  # 百度DNS
        "119.29.29.29",  # 腾讯DNS
        "114.114.114.114",  # 114DNS
        "8.8.8.8",  # 谷歌DNS
    ]
    for dns in dns_servers if dns_servers else default_dns:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(2)
                s.connect((dns, 80))
                return s.getsockname()[0]
        except (socket.timeout, OSError, Exception):
            continue
        finally:
            if isinstance(s, socket.socket):
                s.close()
    return ""
