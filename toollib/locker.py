"""
@author axiner
@version v1.0.0
@created 2022/10/28 14:03
@abstract 锁
@description
@history
"""
import time
import typing as t

try:
    from redis.exceptions import WatchError
except ImportError:
    raise

__all__ = [
    'Locker',
]


class Locker:
    """
    锁，基于redis的分布式锁

    e.g.::

        a = 0
        locker = Locker(redis_cli)  # 创建锁实例
        if locker.acquire(acquire_timeout=2)  # 获取锁
            for i in range(10):
                a += 1
                print(f'a: {a}')
            locker.release()  # 释放锁

        # 另：with方式
        a = 0
        locker = Locker(redis_cli, acquire_timeout=2)
        with locker:
            if locker.is_lock:  # 若获取锁
                for i in range(10):
                    a += 1
                    print(f'a: {a}')

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            redis_cli,
            acquire_timeout: int = 2,
            timeout: int = 29,
            lock_name: str = 'locker',
            lock_value: str = 'locker!@#',
    ):
        """
        初始化
        :param redis_cli: redis客户端对象
        :param acquire_timeout: 获取锁的超时时间
        :param timeout: 锁的过期时间
        :param lock_name: 锁名
        :param lock_value: 锁值
        """
        self.rds = redis_cli
        self.acquire_timeout = acquire_timeout
        self.timeout = timeout
        self.lock_name = lock_name if lock_name else 'locker'
        self.lock_value = lock_value if lock_value else 'locker!@#'
        self.is_lock = False

    def acquire(self, acquire_timeout: t.Union[int, float] = None, timeout: int = None) -> bool:
        """
        获取锁
        :param acquire_timeout: 获取锁的超时时间
        :param timeout: 锁的过期时间
        :return:
        """
        if acquire_timeout is not None:
            self.acquire_timeout = acquire_timeout
        if timeout is not None:
            self.timeout = timeout
        self._acquire_lock()
        return self.is_lock

    def _acquire_lock(self):
        end_time = time.time() + self.acquire_timeout
        while time.time() < end_time:
            if self.rds.set(self.lock_name, self.lock_value, ex=self.timeout, nx=True):
                self.is_lock = True
                break
            elif self.rds.ttl(self.lock_name) == -1:
                self.rds.expire(self.lock_name, self.timeout)
            time.sleep(0.002)

    __enter__ = acquire

    def release(self):
        """
        释放锁
        :return:
        """
        if not self.is_lock:
            return
        with self.rds.pipeline() as pipe:
            while 1:
                try:
                    pipe.watch(self.lock_name)
                    lock_value = pipe.get(self.lock_name)
                    if isinstance(lock_value, bytes):
                        lock_value = lock_value.decode()
                    if not lock_value:
                        break
                    elif lock_value == self.lock_value:
                        pipe.multi()
                        pipe.delete(self.lock_name)
                        pipe.execute()
                        break
                except WatchError:
                    pipe.unwatch()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
