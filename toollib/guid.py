"""
@author axiner
@version v1.0.0
@created 2022/7/30 16:07
@abstract 全局唯一id
@description
@history
"""
import time
from datetime import datetime, timedelta

import typing as t

from toollib.common.error import SystemClockError
from toollib.utils import Singleton, now2timestr

__all__ = [
    'SnowFlake',
    'RedisUid',
]


NoneType = type(None)


class SnowFlake(metaclass=Singleton):
    """
    雪花算法（全局唯一id）

    # 最早是Twitter公司在其内部用于分布式环境下生成唯一ID

    # Twitter's Snowflake algorithm implementation which is used to generate distributed IDs.

    # https://github.com/twitter-archive/snowflake/blob/snowflake-2010/src/main/scala/com/twitter/service/snowflake/IdWorker.scala

    e.g.::

        from toollib.guid import SnowFlake
        snow_cli = SnowFlake()
        uid = snow_cli.gen_uid()

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            worker_id: int = 0,
            datacenter_id: int = 0,
            sequence=0,
            epoch_timestamp: int = 1288834974657,
            worker_id_bits: int = 5,
            datacenter_id_bits: int = 5,
            sequence_bits: int = 12,
            to_str: bool = False,
    ):
        """
        初始化

        注：分布式可通过映射指定不同的'worker_id'+'datacenter_id'来区分

        :param worker_id: 机器ID
        :param datacenter_id: 数据中心ID
        :param sequence: 序号
        :param epoch_timestamp: 纪元（Twitter(1288834974657): 2010-11-04 09:42:54.657000）
        :param worker_id_bits: 机器id位数
        :param datacenter_id_bits: 服务id位数
        :param sequence_bits: 序号位数
        :param to_str: 是否转为字符串
        """
        if not isinstance(worker_id, (int, type(None))):
            raise TypeError('"worker_id" only supported: int')
        if not isinstance(datacenter_id, (int, type(None))):
            raise TypeError('"datacenter_id" only supported: int')
        max_worker_id = -1 ^ (-1 << worker_id_bits)
        max_datacenter_id = -1 ^ (-1 << datacenter_id_bits)
        if worker_id > max_worker_id or worker_id < 0:
            raise ValueError(f'"worker_id" only supported: 0 ~ {max_worker_id}')
        if datacenter_id > max_datacenter_id or datacenter_id < 0:
            raise ValueError(f'"datacenter_id" only supported: 0 ~ {max_datacenter_id}')

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.epoch_timestamp = epoch_timestamp
        self.last_timestamp = -1

        self.worker_id_shift = sequence_bits
        self.datacenter_id_shift = sequence_bits + worker_id_bits
        self.timestamp_left_shift = sequence_bits + worker_id_bits + datacenter_id_bits
        self.sequence_mask = -1 ^ (-1 << sequence_bits)

        self.to_str = to_str

    def gen_uid(self, to_str: bool = None):
        """
        生成唯一id
        :param to_str: 是否转为字符串(可覆盖cls中的to_str)
        :return:
        """
        if to_str is None:
            to_str = self.to_str
        timestamp = self._current_timestamp()
        if timestamp < self.last_timestamp:
            raise SystemClockError("Clock moved backwards. Refusing to generate id for %s milliseconds" % (
                    self.last_timestamp - timestamp))
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                timestamp = self._til_next_millis(self.last_timestamp)
        else:
            self.sequence = 0
        self.last_timestamp = timestamp
        uid = ((timestamp - self.epoch_timestamp) << self.timestamp_left_shift) | \
              (self.datacenter_id << self.datacenter_id_shift) | \
              (self.worker_id << self.worker_id_shift) | self.sequence
        if to_str is True:
            uid = str(uid)
        return uid

    def _til_next_millis(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    @staticmethod
    def _current_timestamp():
        return int(time.time() * 1000)


class RedisUid:
    """
    全局唯一id，基于redis实现（可用于分布式）

    e.g.::

        from toollib.guid import RedisUid

        ruid_cli = RedisUid(redis_cli, prefix='ABC')
        uid = ruid_cli.gen_uid()

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            redis_cli,
            prefix: str = None,
            seq_name: str = None,
            seq_beg: int = 0,
            seq_len: int = 9,
            seq_ex: datetime = None,
            date_fmt: t.Union[str, NoneType] = '%Y%m%d',
            sep: str = '',
    ):
        """
        初始化
        :param redis_cli: redis客户端
        :param prefix: 前缀，为空则没有前缀拼接
        :param seq_name: 序列名称，作为redis存储键(为空则默认取prefix，但两者不能同时为空)
        :param seq_beg: 序列开始，默认为0
        :param seq_len: 序列长度，默认为9(不足则0填充)
        :param seq_ex: 序列过期时间，为空则默认第二天凌晨
        :param date_fmt: 日期格式，为空则没有日期拼接
        :param sep: 分隔符，默认为空
        """
        self.redis_cli = redis_cli
        self.prefix = prefix
        self.seq_name = seq_name or self.prefix
        self.seq_beg = seq_beg
        self.seq_len = seq_len
        self.seq_ex = seq_ex
        self.date_fmt = date_fmt
        self.sep = sep
        self._check_params()

    def _check_params(self):
        if not isinstance(self.prefix, (str, NoneType)):
            raise TypeError("'prefix'只支持字符串型与None")
        if not isinstance(self.seq_name, (str, NoneType)):
            raise TypeError("'seq_name'只支持字符串型与None")
        if not self.seq_name:
            raise ValueError("'prefix'与'seq_name'不能同时为空")
        if not isinstance(self.seq_beg, int):
            raise TypeError("'seq_beg'只支持整型")
        if self.seq_ex is not None and not isinstance(self.seq_ex, datetime):
            raise TypeError("'seq_ex'只支持datetime型")
        if not isinstance(self.sep, str):
            raise TypeError("'sep'只支持字符串型")

    def gen_uid(self, seq_step: int = 1):
        """
        生成唯一id
        :param seq_step: 序列步长，默认为1
        :return:
        """
        if not isinstance(seq_step, int):
            raise TypeError("'seq_step'只支持整型")
        if self.redis_cli.ttl(self.seq_name) < 0:
            self.redis_cli.set(self.seq_name, self.seq_beg)
            self.redis_cli.expireat(self.seq_name, self._set_ex(self.seq_ex))
        _prefix = self.prefix or ''
        _date_value = now2timestr(self.date_fmt) if self.date_fmt else ''
        _seq_value = self.redis_cli.incrby(self.seq_name, seq_step)
        uid = self.sep.join([
            _prefix,
            _date_value,
            str(_seq_value).zfill(self.seq_len)]).lstrip(self.sep)
        return uid

    @staticmethod
    def _set_ex(ex):
        if not ex:
            ex = (datetime.now() + timedelta(days=1)).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        return ex
