import os
from pathlib import Path

import yaml

from toollib.utils import get_cls_attrs, parse_variable, VConvert


class YamlConfig:
    """
    yaml 配置

    e.g.::

        class Config(YamlConfig):
            xxx1: int = 1
            xxx2: str = "abc"


        config = Config(yaml_path="/tmp/yaml_path")
        config.setup()  # 设置
        print(config.xxx1)

        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, yaml_path: str | Path | None = None, yaml_encoding: str = "utf-8", require_yaml: bool = True):
        self._yaml_path = Path(yaml_path) if yaml_path is not None else None
        self._yaml_encoding = yaml_encoding
        self._yaml_cache = None
        if require_yaml:
            if not self._yaml_path or not self._yaml_path.is_file():
                raise FileNotFoundError("'yaml_path' is required and must point to an existing YAML file")

    def setup(
            self,
            prefer_env: bool = True,
            clear_cache: bool = True,
            v_converts: dict[str, VConvert] = None,
            v_invalid: tuple = (None, ""),
            sep: str = ",",
            kv_sep: str = ":",
            is_raise: bool = False,
    ):
        """
        设置
        :param prefer_env: 优先env
        :param clear_cache: 清除缓存
        :param v_converts: 值转换
        :param v_invalid: 值无效
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param is_raise: 是否raise
        :return:
        """
        v_converts = v_converts or {}
        for k, item in get_cls_attrs(self.__class__).items():
            v_type, v = item
            if callable(v_type):
                if prefer_env and k in os.environ:
                    v_from = os.environ
                else:
                    v_from = self.load_yaml()
                v = parse_variable(
                    k=k,
                    v_type=v_type,
                    v_from=v_from,
                    default=v,
                    v_convert=v_converts.get(k),
                    v_invalid=v_invalid,
                    sep=sep,
                    kv_sep=kv_sep,
                    is_raise=is_raise
                )
            setattr(self, k, v)
        if clear_cache:
            self._yaml_cache = None
        return self

    def load_yaml(self, reload: bool = False) -> dict:
        if not self._yaml_path:
            return {}
        if self._yaml_cache is not None and not reload:
            return self._yaml_cache
        with open(self._yaml_path, mode="r", encoding=self._yaml_encoding) as f:
            self._yaml_cache = yaml.load(f, Loader=yaml.FullLoader) or {}
            return self._yaml_cache
