import json
import urllib.request as request


def pkg_lver(pkg_name: str) -> str:
    """
    包的最新版本

    e.g.::

        v = utils.pkg_lver("toollib")

        +++++[更多详见参数或源码]+++++

    :param pkg_name: 包名
    :return:
    """
    try:
        with request.urlopen(f"https://pypi.org/pypi/{pkg_name}/json") as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data["info"]["version"]
            else:
                raise Exception(f"Failed to fetch data. Status code: {resp.status}")
    except Exception:
        raise
