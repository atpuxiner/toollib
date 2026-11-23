"""
@author axiner
@version v1.0.0
@created 2023/5/20 13:19
@abstract 日志-logging
@description
@history
"""

import atexit
import logging
import logging.handlers
import os
import queue
import traceback
from collections.abc import Callable
from contextlib import suppress
from contextvars import ContextVar
from pathlib import Path
from typing import Literal

try:
    import orjson as json

    _has_orjson = True
except ImportError:
    import json

    _has_orjson = False

__all__ = [
    "LogFormatter",
    "ContextVarsFilter",
    "init_logger",
]

_LISTENERS: dict = {}
_QUEUES: dict = {}


class LogFormatter(logging.Formatter):
    def __init__(
        self,
        fmt="%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s",
        datefmt=None,
        style="%",
        validate=True,
        *,
        defaults=None,
        context_vars: dict[str, ContextVar] | None = None,
        serialize: bool = False,
    ):
        self.context_vars = context_vars or {}
        self.serialize = serialize
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self, record):
        if self.serialize:
            log_entry = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "filename": record.filename,
                "lineno": record.lineno,
                "message": record.getMessage(),
            }
            for key in self.context_vars:
                log_entry[key] = getattr(record, key, "N/A")
            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                log_entry["exception"] = {
                    "type": None if exc_type is None else exc_type.__name__,
                    "value": str(exc_value),
                    "stacktrace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                }
            elif record.exc_text:
                log_entry["exception"] = {"stacktrace": record.exc_text}
            if _has_orjson:
                return json.dumps(log_entry, default=str).decode("utf-8")  # type: ignore
            return json.dumps(log_entry, ensure_ascii=False, default=str)  # type: ignore
        else:
            return super().format(record)


class ContextVarsFilter(logging.Filter):
    """
    上下文变量过滤器（把 ContextVar 值注入日志记录）

    :note: 注入发生在记录日志的线程（而非格式化线程），因此兼容 enqueue 队列模式；
        挂在 handler 上时，子 logger 传播过来的记录同样会被注入
    """

    def __init__(self, context_vars: dict[str, ContextVar] | None = None):
        self.context_vars = context_vars or {}
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        for key, var in self.context_vars.items():
            try:
                value = var.get()
            except LookupError:
                value = "N/A"
            setattr(record, key, value)
        return True


def init_logger(
    name: str | None = None,
    level: str | int = "INFO",
    context_vars: dict[str, ContextVar] | None = None,
    fmt: str = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s",
    datefmt: str | None = None,
    msecfmt: str = "%s.%03d",
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
    rotation: Literal["time", "size"] = "time",
    backup_count: int = 30,
    when: Literal["s", "m", "h", "d", "midnight", "w0", "w1", "w2", "w3", "w4", "w5", "w6"] = "midnight",
    interval: int = 1,
    max_bytes: int = 1024 * 1024 * 50,
    propagate: bool = False,
    enqueue: bool = False,
    queue_maxsize: int = 5000,
    **kwargs,
) -> logging.Logger:
    """
    初始化日志器

    e.g.::

        # 初始化
        from toollib import log

        logger = log.init_logger()
        logger.info("hello")

        # 其他模块调用建议
        import logging

        logger = logging.getLogger(__name__)
        logger.info("hello")

        # 上下文变量（如 request_id / client_ip）
        from contextvars import ContextVar

        request_id_var = ContextVar("request_id", default="-")
        client_ip_var = ContextVar("client_ip", default="-")
        logger = log.init_logger(
            context_vars={"request_id": request_id_var, "client_ip": client_ip_var},
            fmt="%(asctime)s %(levelname)s %(request_id)s %(client_ip)s %(name)s %(filename)s:%(lineno)d %(message)s",
        )

        +++++[更多详见参数或源码]+++++

    :param name: 名称
    :param level: 日志等级
    :param context_vars: 上下文变量映射（如 {"request_id": request_id_var, "client_ip": client_ip_var}），fmt 需含对应 %(key)s 占位符
    :param fmt: 日志格式
    :param datefmt: 时间格式
    :param msecfmt: 时间毫秒格式
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
    :param backup_count: 轮转备份数
    :param when: 轮转时间
    :param interval: 轮转间隔
    :param max_bytes: 轮转最大字节
    :param propagate: 向上传播
    :param enqueue: 启用队列
    :param queue_maxsize: 队列最大容量
    :param kwargs
    """
    if not enable_console and not enable_file:
        raise ValueError("enable_file and enable_console cannot both be False")

    logger = logging.getLogger(name)
    if clear_handlers:
        logger.handlers.clear()
    logger.setLevel(level=level)
    # 过滤器必须挂在记录日志一侧的 handler 上（enqueue 时是 QueueHandler，否则是实际 handler），
    # 这样上下文在入队前注入；若挂到监听线程的 handler 上，会读到错误线程的 ContextVar
    context_filter = ContextVarsFilter(context_vars) if context_vars else None

    if not formatter:
        if msecfmt:
            LogFormatter.default_msec_format = msecfmt
        formatter = LogFormatter(
            fmt=fmt,
            datefmt=datefmt,
            serialize=serialize,
            context_vars=context_vars,
        )

    actual_handlers = []

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        actual_handlers.append(console_handler)

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

        def make_handler(filename):
            if rotation == "time":
                handler = logging.handlers.TimedRotatingFileHandler(
                    filename=filename,
                    encoding=encoding,
                    backupCount=backup_count,
                    when=when,
                    interval=interval,
                )
            else:
                handler = logging.handlers.RotatingFileHandler(
                    filename=filename,
                    encoding=encoding,
                    backupCount=backup_count,
                    maxBytes=max_bytes,
                )
            handler.setFormatter(formatter)
            return handler

        access_handler = make_handler(log_access_file)
        access_handler.setLevel(logging.DEBUG)
        actual_handlers.append(access_handler)

        error_handler = make_handler(log_error_file)
        error_handler.setLevel(logging.ERROR)
        actual_handlers.append(error_handler)

    if enqueue:
        key = name or "__root__"
        if key not in _QUEUES:
            log_queue = _Queue(maxsize=queue_maxsize)
            _QUEUES[key] = log_queue
            listener = logging.handlers.QueueListener(log_queue, *actual_handlers, respect_handler_level=True)
            listener.start()
            _LISTENERS[key] = listener

            def _stop_listener():
                with suppress(Exception):
                    listener.stop()

            atexit.register(_stop_listener)

        queue_handler = logging.handlers.QueueHandler(_QUEUES[key])
        queue_handler.setLevel(logging.DEBUG)
        if context_filter:
            queue_handler.addFilter(context_filter)
        logger.addHandler(queue_handler)
    else:
        for h in actual_handlers:
            if context_filter:
                h.addFilter(context_filter)
            logger.addHandler(h)

    logger.propagate = propagate

    return logger


class _Queue(queue.Queue):
    def put(self, item, block=True, timeout=None):
        try:
            super().put(item, block=False)
        except queue.Full:
            with suppress(queue.Empty):
                self.get_nowait()
            with suppress(queue.Full):
                super().put(item, block=False)
