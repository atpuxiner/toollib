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

__all__ = ['init_logger']

default_config = {
    "file_infoname": "info.log",
    "file_errorname": "error.log",
    "file_encoding": "utf-8",
    "file_format": "%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s",
    "file_maxBytes": 1024 * 1024 * 50,
    "file_when": "midnight",
    "file_interval": 1,
    "file_backupCount": 15,
}


def init_logger(
        name: str = None,
        debug: bool = True,
        format: str = "%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        config: dict = None,
        log_dir: str = None,
        is_file: bool = True,
        is_console: bool = True,
        is_time_rotating: bool = False,
        is_disable_existing_logger: bool = False
):
    """
    初始化日志器

    e.g.::

        # 直接使用
        from toollib import log
        logger = log.init_logger(__name__)
        # # 后续直接引用logger对象即可

        # 另：可先初始化，再使用
        # 1. 入口模块初始化
        from toollib import log
        log.init_logger()
        # 2. 其他模块通过logging获取日志器
        import logging
        logger = logging.getLogger(__name__)

        +++++[更多详见参数或源码]+++++

    config: dict
        - file_infoname: 文件info名称
        - file_errorname: 文件error名称
        - file_encoding: 文件编码
        - file_format: 文件日志格式
        - file_maxBytes: 文件轮转最大字节
        - file_when: 文件轮转时间
        - file_interval: 文件轮转间隔
        - file_backupCount: 文件轮转备份数

    :param name: 名称
    :param debug: 是否调试
    :param format: 日志格式
    :param datefmt: 时间格式
    :param config: 配置
    :param log_dir: 日志目录
    :param is_file: 是否文件日志
    :param is_console: 是否控制台日志
    :param is_time_rotating: 是否时间日志轮转
    :param is_disable_existing_logger: 是否禁用已存在的日志记录器
    :return:
    """
    root_level = logging.DEBUG if debug is True else logging.INFO
    formatters, handlers = {}, {}
    root_handlers = []
    if any([is_file, is_console]):
        if is_console is True:
            formatters.update(
                console={
                    "format": format,
                    "datefmt": datefmt
                }
            )
            handlers.update(
                console_handler={
                    "level": logging.DEBUG,
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                }
            )
            root_handlers.append("console_handler")
        if is_file is True:
            config = config or {}
            log_dir = log_dir or os.path.join(os.getcwd(), "logs")
            if not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_infoname = config.get("file_infoname") or default_config["file_infoname"]
            file_errorname = config.get("file_errorname") or default_config["file_errorname"]
            file_encoding = config.get("file_encoding") or default_config["file_encoding"]
            file_format = config.get("file_format") or format
            file_maxBytes = config.get("file_maxBytes") or default_config["file_maxBytes"]
            file_when = config.get("file_when") or default_config["file_when"]
            file_interval = config.get("file_interval") or default_config["file_interval"]
            file_backupCount = config.get("file_backupCount") or default_config["file_backupCount"]
            info_file_handler = {
                "level": logging.DEBUG,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "file",
                "filename": os.path.join(log_dir, file_infoname),
                "encoding": file_encoding,
                "maxBytes": file_maxBytes,
                "backupCount": file_backupCount,
            }
            error_file_handler = {
                "level": logging.ERROR,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "file",
                "filename": os.path.join(log_dir, file_errorname),
                "encoding": file_encoding,
                "maxBytes": file_maxBytes,
                "backupCount": file_backupCount,
            }
            if is_time_rotating is True:
                info_file_handler["class"] = "logging.handlers.TimedRotatingFileHandler"
                info_file_handler["when"] = file_when
                info_file_handler["interval"] = file_interval
                info_file_handler.pop("maxBytes")
                error_file_handler["class"] = "logging.handlers.TimedRotatingFileHandler"
                error_file_handler["when"] = file_when
                error_file_handler["interval"] = file_interval
                error_file_handler.pop("maxBytes")
            formatters.update(
                file={
                    "format": file_format or format,
                    "datefmt": datefmt
                }
            )
            handlers.update(
                info_file_handler=info_file_handler,
                error_file_handler=error_file_handler,
            )
            root_handlers.extend(["info_file_handler", "error_file_handler"])
    else:
        formatters.update(
            console={
                "format": format,
                "datefmt": datefmt
            }
        )
        handlers.update(
            console_handler={
                "level": logging.DEBUG,
                "class": "logging.StreamHandler",
                "formatter": "console",
            }
        )
        root_handlers.append("console_handler")
    logging_config = {
        "version": 1,
        "disable_existing_loggers": is_disable_existing_logger,
        "formatters": formatters,
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
