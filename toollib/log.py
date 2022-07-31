"""
@author axiner
@version v1.0.0
@created 2022/7/31 8:59
@abstract
@description
@history
"""
import logging.config
from pathlib import Path

__all__ = [
    'getLogger',
]


def getLogger(name: str = '', level='DEBUG', formatter='default',
              logdir: str = None, infoname: str = 'info.log', errorname: str = 'error.log',
              is_console: bool = True, max_bytes: int = 1024*1024*50, backup_count: int = 5):
    """
    日志
    使用示例：
        from toollib import log
        logger = log.getLogger()
        logger.info('this is log')
        +++++[更多详见参数或源码]+++++
    :param name: 名称
    :param level: 日志等级
    :param formatter: 日志格式（支持：default, standard, simple）
    :param logdir: 日志目录
    :param infoname: info文件名（当logdir指定时生效）
    :param errorname: error文件名（当logdir指定时生效）
    :param is_console: 生成日志文件时是否开启console日志（当logdir指定时生效）
    :param max_bytes: 最大字节数（当logdir指定时生效）
    :param backup_count: 备份数（当logdir指定时生效）
    :return:
    """
    __CONFIG = {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s][%(filename)s:%(lineno)s][%(levelname)s]%(message)s',
            },
            'standard': {
                'format': '[%(asctime)s][%(threadName)s:%(thread)d][task_id:%(name)s][%(filename)s:%(lineno)d]'
                          '[%(levelname)s]%(message)s',
            },
            'simple': {
                'format': '%(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': formatter,
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': level,
                'propagate': False,
            },
        },
        'disable_existing_loggers': True,
    }
    if logdir:
        logDir = Path(logdir).absolute()
        logDir.mkdir(parents=True, exist_ok=True)
        info = {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logDir.joinpath(infoname).as_posix(),
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'formatter': 'standard',
            'encoding': 'utf-8',
        }
        error = {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logDir.joinpath(errorname).as_posix(),
            'maxBytes': max_bytes,
            'backupCount': backup_count,
            'formatter': 'standard',
            'encoding': 'utf-8',
        }
        __CONFIG['handlers'].update({
            'info': info,
            'error': error,
        })
        __handlers = ['info', 'error']
        if is_console is True:
            __handlers.append('console')
        __CONFIG['loggers']['']['handlers'] = __handlers
    logging.config.dictConfig(__CONFIG)
    return logging.getLogger(name)
