import os
from pathlib import Path
from typing import get_origin

import yaml
from dotenv import load_dotenv

from toollib.common.error import ConfFileError
from toollib.utils import VConvert, FrozenVar, get_cls_attrs, parse_variable


class ConfModel:
    """
    配置模型

    e.g.::

        class Config(ConfModel):
            xxx1: int = 1
            xxx2: FrozenVar[str] = "abc"  # FrozenVar 表示冻结变量（跳过处理，此处值为 abc）


        config = Config(dotenv_path="./.env", yaml_path="./xxx.yaml")
        print(config.xxx1)

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            dotenv_path: str | Path | None = None,
            dotenv_encoding: str = "utf-8",
            dotenv_override_sysenv: bool = False,
            dotenv_interpolate: bool = True,
            yaml_path: str | Path | None = None,
            yaml_encoding: str = "utf-8",
            file_prefer_env: bool = True,
            attr_prefer_env: bool = True,
            v_converts: dict[str, VConvert] = None,
            v_invalid: tuple = (None, ""),
            sep: str = ",",
            kv_sep: str = ":",
            is_raise: bool = False,
    ):
        """
        初始化
        :param dotenv_path: .env路径
        :param dotenv_encoding: .env编码
        :param dotenv_override_sysenv: .env覆盖系统env
        :param dotenv_interpolate: .env变量插值
        :param yaml_path: yaml路径
        :param yaml_encoding: yaml编码
        :param file_prefer_env: 文件加载优化env（文件路径、编码等）
        :param attr_prefer_env: 属性加载优先env
        :param v_converts: 值转换
        :param v_invalid: 值无效
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param is_raise: 是否raise
        """
        _dotenv_path = (os.environ.get("dotenv_path") if file_prefer_env else None) or dotenv_path
        if _dotenv_path is not None:
            if not Path(_dotenv_path).is_file():
                raise ConfFileError(
                    f"The specified .env file does not exist or is not a regular file: '{_dotenv_path}'"
                )
            _dotenv_encoding = (os.environ.get("dotenv_encoding") if file_prefer_env else None) or dotenv_encoding
            _dotenv_override_sysenv = (os.environ.get(
                "dotenv_override_sysenv") if file_prefer_env else None) or dotenv_override_sysenv
            _dotenv_interpolate = (os.environ.get(
                "dotenv_interpolate") if file_prefer_env else None) or dotenv_interpolate
            load_dotenv(
                dotenv_path=_dotenv_path,
                encoding=_dotenv_encoding,
                override=_dotenv_override_sysenv,
                interpolate=_dotenv_interpolate,
            )
        self._yaml_path = (os.environ.get("yaml_path") if file_prefer_env else None) or yaml_path
        if self._yaml_path is not None and not Path(self._yaml_path).is_file():
            raise ConfFileError(
                f"The specified yaml file does not exist or is not a regular file: '{self._yaml_path}'"
            )
        self._yaml_encoding = (os.environ.get("yaml_encoding") if file_prefer_env else None) or yaml_encoding
        self._yaml_cache = None
        self.load(
            attr_prefer_env=attr_prefer_env,
            v_converts=v_converts,
            v_invalid=v_invalid,
            sep=sep,
            kv_sep=kv_sep,
            is_raise=is_raise,
        )

    def load(
            self,
            attr_prefer_env: bool = True,
            v_converts: dict[str, VConvert] = None,
            v_invalid: tuple = (None, ""),
            sep: str = ",",
            kv_sep: str = ":",
            is_raise: bool = False,
            yaml_reload: bool = True,
            clean_cache: bool = True,
    ):
        """
        加载
        :param attr_prefer_env: 属性加载优先env
        :param v_converts: 值转换
        :param v_invalid: 值无效
        :param sep: 分隔符，针对list、tuple、set、dict
        :param kv_sep: 键值分隔符，针对dict
        :param is_raise: 是否raise
        :param yaml_reload: yaml重新加载
        :param clean_cache: 清除缓存
        :return:
        """
        v_converts = v_converts or {}
        for k, item in get_cls_attrs(self.__class__).items():
            v_type, v = item
            if get_origin(v_type) is FrozenVar:
                continue
            if callable(v_type):
                if attr_prefer_env and k in os.environ:
                    v_from = os.environ
                else:
                    v_from = self._load_yaml(yaml_reload)
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
