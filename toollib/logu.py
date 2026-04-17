"""
@author axiner
@version v1.0.0
@created 2023/5/20 13:19
@abstract 日志-loguru
@description
@history
"""

import logging
import os
import sys
import traceback
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path

from loguru import logger
from loguru._logger import Logger

try:
    import orjson as json

    _has_orjson = True
except ImportError:
    import json

    _has_orjson = False

__all__ = [
    "LogFormatter",
    "InterceptionHandler",
    "init_logger",
]


class LogFormatter:
    def __init__(
        self,
        fmt: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {name} {file}:{line} {message}",
        datefmt: str = "%Y-%m-%d %H:%M:%S.%f",
        msecfmt: int = 3,
        request_id_var: ContextVar | None = None,
        fmt_with_request_id: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[request_id]} {name} {file}:{line} {message}",
        serialize: bool = False,
    ):
        self.fmt = fmt
        self.datefmt = datefmt
        self.msecfmt = msecfmt
        self.request_id_var = request_id_var
        if self.request_id_var:
            self.fmt = fmt_with_request_id
        if self.fmt:
            self.fmt = self.fmt.rstrip("\n") + "\n"
        self.serialize = serialize

    def __call__(self, record, *args, **kwargs):
        if self.request_id_var:
            try:
                request_id = self.request_id_var.get()
            except LookupError:
                request_id = "N/A"
            record["extra"].setdefault("request_id", request_id)
        if self.serialize:
            timestamp = record["time"].strftime(self.datefmt)
            if ".%f" in self.datefmt:
                timestamp = timestamp[: -self.msecfmt].rstrip(".")
            log_entry = {
                "timestamp": timestamp,
                "level": record["level"].name,
                "logger": record["name"],
                "filename": record["file"].name,
                "lineno": record["line"],
                "message": record["message"],
            }
            if request_id := record["extra"].get("request_id"):
                log_entry["request_id"] = request_id
            if exc := record.get("exception"):
                log_entry["exception"] = {
                    "type": None if exc.type is None else exc.type.__name__,
                    "value": exc.value,
                    "stacktrace": "".join(traceback.format_exception(exc.type, exc.value, exc.traceback)),
                }
            if _has_orjson:
                record["extra"]["json"] = json.dumps(log_entry, default=str).decode("utf-8")  # type: ignore
            else:
                record["extra"]["json"] = json.dumps(log_entry, ensure_ascii=False, default=str)  # type: ignore
            return "{extra[json]}\n"
        fmt = self.fmt
        if record["exception"] and "{exception}" not in fmt:
            fmt += "{exception}"
        return fmt


class InterceptionHandler(logging.Handler):
    def __init__(
        self,
        max_depth: int = 10,
        fields: tuple | None = (
            "message",
            "levelname",
            "levelno",
            "name",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "asctime",
            "taskName",
        ),
        context: Callable[[], dict] | None = None,
    ):
        super().__init__()
        self.max_depth = max_depth
        self.fields = fields
        self.context = context

    def emit(self, record: logging.LogRecord):

        if record.name.startswith("loguru."):
            return

        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = record.levelno

        frame = sys._getframe().f_back
        depth = 0
        skip_file = os.path.normcase(logging.__file__)
        while frame and depth < self.max_depth:
            if os.path.normcase(frame.f_code.co_filename) != skip_file:
                break
            frame = frame.f_back
            depth += 1

        extra = {k: getattr(record, k, None) for k in self.fields or () if hasattr(record, k)}
        if self.context:
            try:
                ctx = self.context()
                if ctx:
                    extra.update(ctx)
            except Exception:
                pass

        exc = record.exc_info
        if not exc or exc[0] is None:
            exc = None

        logger.opt(
            depth=depth + 1,
            exception=exc,
        ).bind(**extra).log(level, record.getMessage())


def init_logger(
    name: str | None = None,
    level: str | int = "INFO",
    fmt: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {name} {file}:{line} {message}",
    datefmt: str = "%Y-%m-%d %H:%M:%S.%f",
    msecfmt: int = 3,
    request_id_var: ContextVar | None = None,
    fmt_with_request_id: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[request_id]} {name} {file}:{line} {message}",
    serialize: bool = False,
    formatter: Callable | None = None,
    clear_handlers: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    outdir: str | Path | None = None,
    access_name: str = "access.log",
    error_name: str = "error.log",
    name_with_pid: bool = False,
    encoding: str = "utf-8",
    rotation: str = "00:00",
    retention: str = "30 days",
    compression: str | None = None,
    enqueue: bool = True,
    backtrace: bool = False,
    diagnose: bool = False,
    catch: bool = True,
    interception: type[logging.Handler] | None = InterceptionHandler,
    **kwargs,
) -> Logger:
    """
    初始化日志器

    e.g.::

        # 初始化
        from toollib import logu

        logger = logu.init_logger()
        logger.info("hello")

        # 其他模块调用建议
        from loguru import logger

        logger.info("hello")

        +++++[更多详见参数或源码]+++++

    :param name: 名称（无用）
    :param level: 日志等级
    :param fmt: 日志格式
    :param datefmt: 时间格式
    :param msecfmt: 时间毫秒格式
    :param request_id_var: 请求id变量
    :param fmt_with_request_id: 带request_id的日志格式
    :param serialize: 序列化
    :param formatter: 格式化实例
    :param clear_handlers: 清除handlers
    :param enable_console: 开启控制台日志
    :param enable_file: 开启文件日志
    :param outdir: 输出目录
    :param access_name: access名称
    :param error_name: error名称
    :param name_with_pid: 名称带pid
    :param encoding: 编码
    :param rotation: 轮转方式
    :param retention: 保留策略
    :param compression: 压缩方式
    :param enqueue: 启用队列
    :param backtrace: 回溯
    :param diagnose: 诊断
    :param catch: 捕获
    :param interception: 拦截器
    :param kwargs:
        interception_max_depth: int, 最大遍历深度
        interception_fields: tuple, LogRecord字段
        interception_context: Callable, 获取上下文的函数
    """
    if not enable_console and not enable_file:
        raise ValueError("enable_file and enable_console cannot both be False")

    if clear_handlers:
        logger.remove(None)
    if interception:
        root_logger = logging.getLogger()
        if clear_handlers:
            root_logger.handlers.clear()
        root_logger.setLevel(level)
        if interception is InterceptionHandler:
            _interception_kwargs = {}
            if max_depth := kwargs.get("interception_max_depth"):
                _interception_kwargs["max_depth"] = max_depth
            if fields := kwargs.get("interception_fields"):
                _interception_kwargs["fields"] = fields
            if context := kwargs.get("interception_context"):
                _interception_kwargs["context"] = context
            interception_handler = interception(**_interception_kwargs)
        else:
            interception_handler = interception()
        root_logger.addHandler(interception_handler)
    formatter = formatter or LogFormatter(
        fmt=fmt,
        datefmt=datefmt,
        msecfmt=msecfmt,
        request_id_var=request_id_var,
        fmt_with_request_id=fmt_with_request_id,
        serialize=serialize,
    )

    if enable_console:
        logger.add(
            sys.stdout,
            format=formatter,
            level=level,
            enqueue=enqueue,
            backtrace=backtrace,
            diagnose=diagnose,
            catch=catch,
        )

    if enable_file:
        outdir = outdir or os.path.join(os.getcwd(), "logs")
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        if name_with_pid:
            pid = os.getpid()
            access_name = f"{pid}-{access_name}"
            error_name = f"{pid}-{error_name}"
        log_access_file = outdir.joinpath(access_name)
        log_error_file = outdir.joinpath(error_name)
        logger.add(
            log_access_file,
            encoding=encoding,
            format=formatter,
            level=level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            enqueue=enqueue,
            backtrace=backtrace,
            diagnose=diagnose,
            catch=catch,
        )
        logger.add(
            log_error_file,
            encoding=encoding,
            format=formatter,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression=compression,
            enqueue=enqueue,
            backtrace=backtrace,
            diagnose=diagnose,
            catch=catch,
        )

    return logger
