import os
import sys
from pathlib import Path
from typing import get_origin

import yaml
from dotenv import load_dotenv

from toollib.common.error import ConfModelError
from toollib.utils import VConvert, FrozenVar, Undefined, get_cls_attrs, parse_variable


class ConfModel:
    """
    配置模型

    e.g.::

        class Config(ConfModel):
            attr1: int  # 必填（需在[环境变量/配置文件]中设置）
            attr2: FrozenVar[str] = "abc"  # 冻结（忽略[环境变量/配置文件]直接为初始值）
            attr3: str = "abc"  # 选填（若[环境变量/配置文件]未设置则为初始值）


        config = Config(dotenv_path="./.env", yaml_path="./xxx.yaml")
        print(config.attr1)

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            dotenv_path: str | Path | None = None,
            dotenv_encoding: str = "utf-8",
            dotenv_override_env: bool = False,
            dotenv_interpolate: bool = True,
            yaml_path: str | Path | None = None,
            yaml_encoding: str = "utf-8",
            file_prefer_env: bool = True,
            attr_prefer_env: bool = True,
            skip_empty_env: bool = True,
            v_converts: dict[str, VConvert] = None,
            sep: str = ",",
            kv_sep: str = ":",
            ignore_unsupported_type: bool = True,
            raise_on_error: bool = False,
    ):
        """
        初始化
        :param dotenv_path: .env路径
        :param dotenv_encoding: .env编码
        :param dotenv_override_env: .env覆盖系统env
        :param dotenv_interpolate: .env变量插值
        :param yaml_path: yaml路径
        :param yaml_encoding: yaml编码
        :param file_prefer_env: 文件加载优化env（文件路径、编码等）
        :param attr_prefer_env: 属性加载优先env
        :param skip_empty_env: 跳过空字符串env
        :param v_converts: 值转换
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param ignore_unsupported_type: 忽略不支持的类型（直接设置）
        :param raise_on_error: 遇错抛异常
        """
        _dotenv_path = (os.environ.get("dotenv_path") if file_prefer_env else None) or dotenv_path
        if _dotenv_path is not None:
            if not Path(_dotenv_path).is_file():
                raise ConfModelError(
                    f"The specified .env file does not exist or is not a regular file: {_dotenv_path!r}"
                )
            _dotenv_encoding = (os.environ.get("dotenv_encoding") if file_prefer_env else None) or dotenv_encoding
            _dotenv_override_env = (os.environ.get(
                "dotenv_override_env") if file_prefer_env else None) or dotenv_override_env
            _dotenv_interpolate = (os.environ.get(
                "dotenv_interpolate") if file_prefer_env else None) or dotenv_interpolate
            load_dotenv(
                dotenv_path=_dotenv_path,
                encoding=_dotenv_encoding,
                override=_dotenv_override_env,
                interpolate=_dotenv_interpolate,
            )
        self._yaml_path = (os.environ.get("yaml_path") if file_prefer_env else None) or yaml_path
        if self._yaml_path is not None and not Path(self._yaml_path).is_file():
            raise ConfModelError(
                f"The specified yaml file does not exist or is not a regular file: {self._yaml_path!r}"
            )
        self._yaml_encoding = (os.environ.get("yaml_encoding") if file_prefer_env else None) or yaml_encoding
        self._yaml_cache = None
        self.load(
            attr_prefer_env=attr_prefer_env,
            skip_empty_env=skip_empty_env,
            v_converts=v_converts,
            sep=sep,
            kv_sep=kv_sep,
            ignore_unsupported_type=ignore_unsupported_type,
            raise_on_error=raise_on_error,
        )

    def load(
            self,
            attr_prefer_env: bool = True,
            skip_empty_env: bool = True,
            v_converts: dict[str, VConvert] = None,
            sep: str = ",",
            kv_sep: str = ":",
            ignore_unsupported_type: bool = True,
            raise_on_error: bool = False,
            yaml_reload: bool = True,
            clean_cache: bool = True,
    ):
        """
        加载
        :param attr_prefer_env: 属性加载优先env
        :param skip_empty_env: 跳过空字符串env
        :param v_converts: 值转换
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param ignore_unsupported_type: 忽略不支持的类型（直接设置）
        :param raise_on_error: 遇错抛异常
        :param yaml_reload: yaml重新加载
        :param clean_cache: 清除缓存
        :return:
        """
        v_converts = v_converts or {}
        _os_environ = {
            alias: os.environ[k]
            for k in get_cls_attrs(self.__class__)
            if k in os.environ
            if not (skip_empty_env and os.environ[k] == "")
            for alias in ([k, k.lower(), k.upper()] if sys.platform.startswith("win") else [k])
        }
        for k, item in get_cls_attrs(self.__class__).items():
            v_type, v = item
            if get_origin(v_type) is FrozenVar:
                if v is Undefined:
                    raise ConfModelError(f"Undefined required frozen variable: {k!r}")
                continue
            if attr_prefer_env and k in _os_environ:
                v_from = _os_environ
            else:
                v_from = self._load_yaml(yaml_reload)
            v = parse_variable(
                k=k,
                v_type=v_type,
                v_from=v_from,
                default=v,
                v_convert=v_converts.get(k),
                sep=sep,
                kv_sep=kv_sep,
                ignore_unsupported_type=ignore_unsupported_type,
                raise_on_error=raise_on_error,
            )
            if v is Undefined:
                raise ConfModelError(f"Missing required configuration: {k!r}")
            setattr(self, k, v)
        if clean_cache:
            self._yaml_cache = None
        return self

    def _load_yaml(self, reload: bool = False) -> dict:
        if not self._yaml_path:
            return {}
        if self._yaml_cache is not None and not reload:
            return self._yaml_cache
        with open(self._yaml_path, mode="r", encoding=self._yaml_encoding) as f:
            self._yaml_cache = yaml.load(f, Loader=yaml.FullLoader) or {}
            return self._yaml_cache
