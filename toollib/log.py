"""
@author axiner
@version v1.0.0
@created 2023/5/20 13:19
@abstract 日志
@description
@history
"""
import logging.config
import os
from contextvars import ContextVar

__all__ = ['init_logger']


class RequestContextFormatter(logging.Formatter):
    def __init__(
            self,
            fmt=None,
            datefmt=None,
            style='%',
            validate=True,
            *,
            defaults=None,
            request_id_var: ContextVar = None,
            fmt_with_request_id: str = None,
    ):
        self.request_id_var = request_id_var
        if self.request_id_var:
            fmt = fmt_with_request_id
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self, record):
        if self.request_id_var:
            try:
                request_id = self.request_id_var.get()
            except LookupError:
                request_id = "N/A"
            record.request_id = request_id
        return super().format(record)


def init_logger(
        name: str = None,
        debug: bool = False,
        fmt: str = "%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s",
        fmt_with_request_id: str = "%(asctime)s.%(msecs)03d %(levelname)s %(request_id)s %(filename)s:%(lineno)d %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        force_clear: bool = True,
        propagate: bool = False,
        request_id_var: ContextVar = None,
        enable_console: bool = True,
        enable_file: bool = True,
        log_dir: str = None,
        access_name: str = "access.log",
        error_name: str = "error.log",
        time_rotating: bool = False,
        encoding: str = "utf-8",
        backup_count: str = 15,
        when: str = "midnight",
        interval: str = 1,
        max_bytes: str = 1024 * 1024 * 50,
):
    """
    初始化日志器

    e.g.::

        # 初始化
        from toollib import log

        logger = log.init_logger(__name__)
        logger.info("hello")

        +++++[更多详见参数或源码]+++++

    :param name: 名称
    :param debug: 是否调试
    :param fmt: 日志格式
    :param fmt_with_request_id: 带request_id的日志格式
    :param datefmt: 时间格式
    :param force_clear: 强制清除
    :param propagate: 向上传播
    :param request_id_var: 请求id变量
    :param enable_console: 开启控制台日志
    :param enable_file: 开启文件日志
    :param log_dir: 日志目录
    :param access_name: access名称
    :param error_name: error名称
    :param time_rotating: 时间轮转
    :param encoding: 编码
    :param backup_count: 轮转备份数
    :param when: 轮转时间
    :param interval: 轮转间隔
    :param max_bytes: 轮转最大字节
    """
    if not enable_console and not enable_file:
        raise ValueError("enable_file and enable_console cannot both be False")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if force_clear:
        logger.handlers.clear()
    formatter = RequestContextFormatter(
        fmt=fmt,
        datefmt=datefmt,
        request_id_var=request_id_var,
        fmt_with_request_id=fmt_with_request_id,
    )

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

    if enable_file:
        log_dir = log_dir or os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        def make_handler(filename):
            if time_rotating:
                handler = logging.handlers.TimedRotatingFileHandler(
                    filename=os.path.join(log_dir, filename),
                    encoding=encoding,
                    backupCount=backup_count,
                    when=when,
                    interval=interval,
                )
            else:
                handler = logging.handlers.RotatingFileHandler(
                    filename=os.path.join(log_dir, filename),
                    encoding=encoding,
                    backupCount=backup_count,
                    maxBytes=max_bytes,
                )
            handler.setFormatter(formatter)
            return handler

        access_handler = make_handler(access_name)
        access_handler.setLevel(logging.DEBUG)
        logger.addHandler(access_handler)

        error_handler = make_handler(error_name)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

    logger.propagate = propagate

    return logger
