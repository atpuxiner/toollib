import os
import sys
from pathlib import Path
from typing import get_origin

import yaml
from dotenv import load_dotenv

from toollib.common.error import ConfModelError
from toollib.utils import FrozenVar, Undefined, VConverter, get_cls_attrs, parse_variable


class ConfModel:
    """
    配置模型

    e.g.::

        class Config(ConfModel):
            attr1: int  # 必填（需在[环境变量/配置文件]中设置）
            attr2: FrozenVar[str] = "abc"  # 冻结（忽略[环境变量/配置文件]直接为初始值）
            attr3: str = "abc"  # 选填（若[环境变量/配置文件]未设置则为初始值）

        # 注：
        #   - 参数 `prefer_env_attr` 优先env属性，如果环境变量中存在直接获取，否则从 v_from 中获取
        #   - 参数 `v_from` 值来源（默认从yaml文件加载），支持任意 dict（可从数据库等获取）
        config = Config(yaml_path="./xxx.yaml", prefer_env_attr=True)
        print(config.attr1)

        +++++[更多详见参数或源码]+++++
    """

    def __getattr__(self, name: str):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self.__dict__[name] = value

    def __delattr__(self, name: str):
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from None

    def __init__(
        self,
        dotenv_path: str | Path | None = None,
        dotenv_encoding: str = "utf-8",
        dotenv_override: bool = False,
        dotenv_interpolate: bool = True,
        yaml_path: str | Path | None = None,
        yaml_encoding: str = "utf-8",
        prefer_env_path: bool = False,
        prefer_env_attr: bool = False,
        skip_empty_env: bool = True,
        v_from: dict | None = None,
        v_converters: dict[str, VConverter] | None = None,
        sep: str = ",",
        kv_sep: str = ":",
        ignore_unsupported_type: bool = True,
        raise_on_error: bool = False,
    ):
        """
        初始化
        :param dotenv_path: .env路径
        :param dotenv_encoding: .env编码
        :param dotenv_override: .env覆盖
        :param dotenv_interpolate: .env变量插值
        :param yaml_path: yaml路径
        :param yaml_encoding: yaml编码
        :param prefer_env_path: 优先env路径（文件路径、编码等）
        :param prefer_env_attr: 优先env属性
        :param skip_empty_env: 跳过空字符串env
        :param v_from: 值来源（默认从yaml文件加载）
        :param v_converters: 值转换器
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param ignore_unsupported_type: 忽略不支持的类型（直接设置原值）
        :param raise_on_error: 遇错抛异常
        """
        if prefer_env_path:
            dotenv_path = os.environ.get("DOTENV_PATH") or dotenv_path
        if dotenv_path is not None:
            if not Path(dotenv_path).is_file():
                raise ConfModelError(
                    f"The specified .env file does not exist or is not a regular file: {dotenv_path!r}"
                )
            if prefer_env_path:
                dotenv_encoding = os.environ.get("DOTENV_ENCODING") or dotenv_encoding
                dotenv_override = os.environ.get("DOTENV_OVERRIDE") or dotenv_override
                dotenv_interpolate = os.environ.get("DOTENV_INTERPOLATE") or dotenv_interpolate
            load_dotenv(
                dotenv_path=dotenv_path,
                encoding=dotenv_encoding,
                override=dotenv_override,
                interpolate=dotenv_interpolate,
            )
        self._yaml_path, self._yaml_encoding = yaml_path, yaml_encoding
        if prefer_env_path:
            self._yaml_path = os.environ.get("YAML_PATH") or self._yaml_path
            self._yaml_encoding = os.environ.get("YAML_ENCODING") or self._yaml_encoding
        if self._yaml_path is not None and not Path(self._yaml_path).is_file():
            raise ConfModelError(
                f"The specified yaml file does not exist or is not a regular file: {self._yaml_path!r}"
            )
        self.load(
            prefer_env_attr=prefer_env_attr,
            skip_empty_env=skip_empty_env,
            v_from=v_from,
            v_converters=v_converters,
            sep=sep,
            kv_sep=kv_sep,
            ignore_unsupported_type=ignore_unsupported_type,
            raise_on_error=raise_on_error,
        )

    def load(
        self,
        prefer_env_attr: bool = True,
        skip_empty_env: bool = True,
        v_from: dict | None = None,
        v_converters: dict[str, VConverter] | None = None,
        sep: str = ",",
        kv_sep: str = ":",
        ignore_unsupported_type: bool = True,
        raise_on_error: bool = False,
    ):
        """
        加载
        :param prefer_env_attr: 优先env属性
        :param skip_empty_env: 跳过空字符串env
        :param v_from: 值来源（默认从yaml文件加载）
        :param v_converters: 值转换器
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param ignore_unsupported_type: 忽略不支持的类型（直接设置）
        :param raise_on_error: 遇错抛异常
        :return:
        """
        v_converters = v_converters or {}
        _v_from = v_from if v_from is not None else self.load_yaml()
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
            v_from = _os_environ if prefer_env_attr and k in _os_environ else _v_from
            v = parse_variable(
                k=k,
                v_type=v_type,
                v_from=v_from,
                default=v,
                v_converter=v_converters.get(k),
                sep=sep,
                kv_sep=kv_sep,
                ignore_unsupported_type=ignore_unsupported_type,
                raise_on_error=raise_on_error,
            )
            if v is Undefined:
                raise ConfModelError(f"Missing required configuration: {k!r}")
            setattr(self, k, v)
        return self

    def load_yaml(self) -> dict:
        if not self._yaml_path:
            return {}
        with open(self._yaml_path, mode="r", encoding=self._yaml_encoding) as f:
            return yaml.load(f, Loader=yaml.FullLoader) or {}
