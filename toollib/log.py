"""
@author axiner
@version v1.0.0
@created 2023/5/20 13:19
@abstract
@description
@history
"""
import logging.config
import os

__all__ = ['init_logger']


def init_logger(
        name: str,
        config: dict = None,
        debug: bool = True,
        log_dir: str = None,
        is_file: bool = True,
        is_console: bool = True,
):
    """
    初始化日志器

    e.g.::

        from toollib import log

        logger = log.init_logger(__name__)

        +++++[更多详见参数或源码]+++++

    config: dict
        - file_format: 文件日志格式
        - console_format: 控制台日志格式
        - datefmt: 日期格式
        - info_filename: info日志文件名称
        - error_filename: error日志文件名称
        - file_maxBytes: 文件日志最大字节
        - file_backupCount: 文件日志备份数

    :param name: 名称
    :param config: 配置
    :param debug: 是否调试
    :param log_dir: 日志目录
    :param is_file: 是否文件日志
    :param is_console: 是否控制台日志
    :return:
    """
    config = config or {}
    file_format = config.get("file_format", "%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s")
    console_format = config.get("console_format", "%(asctime)s.%(msecs)03d %(levelname)s %(message)s")
    datefmt = config.get("datefmt", "%Y-%m-%d %H:%M:%S")
    info_filename = config.get("info_filename", "info.log")
    error_filename = config.get("error_filename", "error.log")
    file_maxBytes = config.get("file_maxBytes", 1024*1024*50)
    file_backupCount = config.get("file_backupCount", 10)
    root_level = logging.DEBUG if debug is True else logging.INFO
    log_dir = log_dir or os.path.join(os.getcwd(), "logs")
    handlers, root_handlers = {}, []
    if any([is_file, is_console]):
        if is_file is True:
            if not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            handlers.update(
                info_file_handler={
                    "level": logging.INFO,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(log_dir, info_filename),
                    "maxBytes": file_maxBytes,
                    "backupCount": file_backupCount,
                    "formatter": "file",
                    "encoding": "utf-8",
                },
                error_file_handler={
                    "level": logging.ERROR,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(log_dir, error_filename),
                    "maxBytes": file_maxBytes,
                    "backupCount": file_backupCount,
                    "formatter": "file",
                    "encoding": "utf-8",
                }
            )
            root_handlers.extend(["info_file_handler", "error_file_handler"])
        if is_console is True:
            handlers.update(
                console_handler={
                    "level": logging.DEBUG,
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                }
            )
            root_handlers.append("console_handler")
    else:
        raise ValueError("`is_console`与`is_filelog`至少一个为真")
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "file": {
                "format": file_format,
                "datefmt": datefmt
            },
            "console": {
                "format": console_format,
                "datefmt": datefmt
            }
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "handlers": root_handlers,
                "level": root_level,
                "propagate": True
            }
        }
    }
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(name)
    return logger
