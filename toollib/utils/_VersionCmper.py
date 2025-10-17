import re


class VersionCmper:
    """
    版本比较

    e.g.::

        from toollib.utils import VersionCmper

        ver1 = VersionCmper("1.0.1")
        ver2 = VersionCmper("1.0.2")
        print(ver1 > ver2)  # Out: False

        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, version: str, is_strgtnum: bool = True):
        """
        版本比较
        :param version: 版本号
        :param is_strgtnum: 是否字符串大于数字。比如：True: 1.0.a > 1.0.11
        """
        self.version = version
        self.is_strgtnum = is_strgtnum
        self.parts = self._split_version(version)

    @staticmethod
    def _split_version(version):
        parts = re.split(r'(\d+|[a-zA-Z]+)', version)
        return [int(part) if part.isdigit() else part for part in parts if part]

    def _compare_parts(self, other_parts):
        for part1, part2 in zip(self.parts, other_parts):
            if isinstance(part1, int) and isinstance(part2, int):
                if part1 != part2:
                    return (part1 > part2) - (part1 < part2)
            elif isinstance(part1, str) and isinstance(part2, str):
                if part1 != part2:
                    return (part1 > part2) - (part1 < part2)
            else:
                if self.is_strgtnum:
                    return 1 if isinstance(part1, str) else -1
                else:
                    return 1 if isinstance(part1, int) else -1
        return (len(self.parts) > len(other_parts)) - (len(self.parts) < len(other_parts))

    def __eq__(self, other):
        return self._compare_parts(other.parts) == 0

    def __lt__(self, other):
        return self._compare_parts(other.parts) < 0

    def __le__(self, other):
        return self._compare_parts(other.parts) <= 0

    def __gt__(self, other):
        return self._compare_parts(other.parts) > 0

    def __ge__(self, other):
        return self._compare_parts(other.parts) >= 0

    def __ne__(self, other):
        return self._compare_parts(other.parts) != 0
