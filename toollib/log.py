"""
@author axiner
@version v1.0.0
@created 2023/5/20 13:19
@abstract 日志-logging
@description
@history
"""
import logging
import logging.handlers
import os
import atexit
import queue
import traceback
from contextvars import ContextVar
from pathlib import Path
from typing import Literal, Callable

try:
    import orjson as json
    _has_orjson = True
except ImportError:
    import json
    _has_orjson = False

__all__ = [
    'LogFormatter',
    'init_logger',
]

_LISTENERS: dict = {}
_QUEUES: dict = {}


class LogFormatter(logging.Formatter):

    def __init__(
            self,
            fmt="%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s",
            datefmt=None,
            style='%',
            validate=True,
            *,
            defaults=None,
            request_id_var: ContextVar = None,
            fmt_with_request_id: str = "%(asctime)s %(levelname)s %(request_id)s %(name)s %(filename)s:%(lineno)d %(message)s",
            serialize: bool = False,
    ):
        self.request_id_var = request_id_var
        if self.request_id_var:
            fmt = fmt_with_request_id
        self.serialize = serialize
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self, record):
        if self.request_id_var:
            try:
                request_id = self.request_id_var.get()
            except LookupError:
                request_id = "N/A"
            record.request_id = request_id
        if self.serialize:
            log_entry = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "filename": record.filename,
                "lineno": record.lineno,
                "message": record.getMessage(),
            }
            if hasattr(record, 'request_id'):
                log_entry["request_id"] = record.request_id
            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                log_entry["exception"] = {
                    "type": None if exc_type is None else exc_type.__name__,
                    "value": str(exc_value),
                    "stacktrace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                }
            elif record.exc_text:
                log_entry["exception"] = {
                    "stacktrace": record.exc_text
                }
            if _has_orjson:
                return json.dumps(log_entry, default=str).decode("utf-8")
            return json.dumps(log_entry, ensure_ascii=False, default=str)
        else:
            return super().format(record)


def init_logger(
        name: str = None,
        level: str | int = "INFO",
        fmt: str = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s",
        datefmt: str = None,
        msecfmt: str = '%s.%03d',
        request_id_var: ContextVar = None,
        fmt_with_request_id: str = "%(asctime)s %(levelname)s %(request_id)s %(name)s %(filename)s:%(lineno)d %(message)s",
        serialize: bool = False,
        formatter: Callable = None,
        clear_handlers: bool = True,
        enable_console: bool = True,
        enable_file: bool = True,
        basedir: str = None,
        access_name: str = "access.log",
        error_name: str = "error.log",
        name_with_pid: bool = False,
        encoding: str = "utf-8",
        rotation: Literal['time', 'size'] = 'time',
        backup_count: int = 30,
        when: Literal['s', 'm', 'h', 'd', 'midnight', 'w0', 'w1', 'w2', 'w3', 'w4', 'w5', 'w6'] = "midnight",
        interval: int = 1,
        max_bytes: int = 1024 * 1024 * 50,
        propagate: bool = False,
        enqueue: bool = False,
        queue_maxsize: int = 5000,
        **kwargs
) -> logging.Logger:
    """
    初始化日志器

    e.g.::

        # 初始化
        from toollib import log

        logger = log.init_logger(__name__)
        logger.info("hello")

        # 其他模块调用建议
        import logging

        logger = logging.getLogger(__name__)
        logger.info("hello")

        +++++[更多详见参数或源码]+++++

    :param name: 名称
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
    :param basedir: 日志基目录
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
    """
    if not enable_console and not enable_file:
        raise ValueError("enable_file and enable_console cannot both be False")

    logger = logging.getLogger(name)
    if clear_handlers:
        logger.handlers.clear()
    logger.setLevel(level=level)
    if not formatter:
        if msecfmt:
            LogFormatter.default_msec_format = msecfmt
        formatter = LogFormatter(
            fmt=fmt,
            datefmt=datefmt,
            serialize=serialize,
            request_id_var=request_id_var,
            fmt_with_request_id=fmt_with_request_id,
        )

    actual_handlers = []

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        actual_handlers.append(console_handler)

    if enable_file:
        basedir = basedir or os.path.join(os.getcwd(), "logs")
        basedir = Path(basedir)
        basedir.mkdir(parents=True, exist_ok=True)
        if name_with_pid:
            pid = os.getpid()
            access_name = f"{pid}-{access_name}"
            error_name = f"{pid}-{error_name}"
        log_access_file = basedir.joinpath(access_name)
        log_error_file = basedir.joinpath(error_name)

        def make_handler(filename):
            if rotation == 'time':
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
            listener = logging.handlers.QueueListener(
                log_queue,
                *actual_handlers,
                respect_handler_level=True
            )
            listener.start()
            _LISTENERS[key] = listener

            def _stop_listener():
                try:
                    listener.stop()
                except Exception:
                    pass

            atexit.register(_stop_listener)

        queue_handler = logging.handlers.QueueHandler(_QUEUES[key])
        queue_handler.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)
    else:
        for h in actual_handlers:
            logger.addHandler(h)

    logger.propagate = propagate

    return logger


class _Queue(queue.Queue):

    def put(self, item, block=True, timeout=None):
        try:
            super().put(item, block=False)
        except queue.Full:
            try:
                self.get_nowait()
            except queue.Empty:
                pass
            try:
                super().put(item, block=False)
            except queue.Full:
                pass
