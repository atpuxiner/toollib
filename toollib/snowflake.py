"""
@author axiner
@version v1.0.0
@created 2022/7/30 16:07
@abstract
@description
@history
"""
# Twitter's Snowflake algorithm implementation which is used to generate distributed IDs.
# https://github.com/twitter-archive/snowflake/blob/snowflake-2010/src/main/scala/com/twitter/service/snowflake/IdWorker.scala
import time

from toollib.common.error import InvalidSystemClock
from toollib.utils import Singleton

__all__ = [
    'SnowFlake',
    'snow',
]


class SnowFlake(metaclass=Singleton):
    """
    雪花算法
    （最早是Twitter公司在其内部用于分布式环境下生成唯一ID）
    使用示例：
        from toollib.snowflake import SnowFlake
        snow = SnowFlake()
        uid = snow.guid()
        或：直接引用该模块的snow对象
        from toollib.snowflake import snow
        uid = snow.guid()
        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, worker_id: int = 0, datacenter_id: int = 0, sequence=0, epoch_timestamp: int = 1288834974657,
                 worker_id_bits: int = 5, datacenter_id_bits: int = 5, sequence_bits: int = 12):
        """
        初始化
            注：分布式可通过映射指定不同的'worker_id'+'datacenter_id'来区分
        :param worker_id: 机器ID
        :param datacenter_id: 数据中心ID
        :param sequence: 序号
        :param epoch_timestamp: 纪元
        :param worker_id_bits: 机器id位数
        :param datacenter_id_bits: 服务id位数
        :param sequence_bits: 序号位数
        """
        if not isinstance(worker_id, (int, type(None))):
            raise TypeError('"worker_id" only supported: int')
        if not isinstance(datacenter_id, (int, type(None))):
            raise TypeError('"datacenter_id" only supported: int')
        max_worker_id = -1 ^ (-1 << worker_id_bits)
        max_datacenter_id = -1 ^ (-1 << datacenter_id_bits)
        if worker_id > max_worker_id or worker_id < 0:
            raise ValueError(f'"worker_id" only supported: 0, {max_worker_id}')
        if datacenter_id > max_datacenter_id or datacenter_id < 0:
            raise ValueError(f'"datacenter_id" only supported: 0, {max_datacenter_id}')

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.epoch_timestamp = epoch_timestamp
        self.last_timestamp = -1

        self.worker_id_shift = sequence_bits
        self.datacenter_id_shift = sequence_bits + worker_id_bits
        self.timestamp_left_shift = sequence_bits + worker_id_bits + datacenter_id_bits
        self.sequence_mask = -1 ^ (-1 << sequence_bits)

    def guid(self, to_str: bool = True):
        timestamp = self._current_timestamp()
        if timestamp < self.last_timestamp:
            raise InvalidSystemClock('clock is moving backwards. Rejecting requests until %s' % self.last_timestamp)
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                timestamp = self._util_next_millis(self.last_timestamp)
        else:
            self.sequence = 0
        self.last_timestamp = timestamp
        nextid = ((timestamp - self.epoch_timestamp) << self.timestamp_left_shift) | \
                 (self.datacenter_id << self.datacenter_id_shift) | \
                 (self.worker_id << self.worker_id_shift) | self.sequence
        if to_str is True:
            nextid = str(nextid)
        return nextid

    def _util_next_millis(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    @staticmethod
    def _current_timestamp():
        return int(time.time() * 1000)


snow = SnowFlake()
