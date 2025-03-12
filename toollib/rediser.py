"""
@author axiner
@version v1.0.0
@created 2022/10/28 14:23
@abstract redis
@description
@history
"""
try:
    import redis
except ImportError:
    raise

__all__ = ['RedisCli']


class RedisCli:
    """
    redis客户端

    e.g.::

        # 创建
        redis_cli = RedisCli(host='127.0.0.1', max_connections=100)
        # 使用方式1
        r = redis_cli.connection()
        value = r.get("xxx")
        # 使用方式2（不推荐）
        value = redis_cli.get("xxx")
        # 使用方式3
        with redis_cli.connection() as r:
            value = r.get("xxx")

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
            self,
            host="localhost",
            port=6379,
            db=0,
            password=None,
            max_connections=None,
            **kwargs,
    ):
        """
        初始化
        :param host: host
        :param port: 端口
        :param db: 数据库
        :param password: 密码
        :param max_connections: 最大连接数
        :param kwargs: 其他参数
        """
        self._redis_pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            **kwargs,
        )
        self._conn = redis.StrictRedis(connection_pool=self._redis_pool)

    def connection(self):
        """
        创建连接
        :return:
        """
        self._conn = redis.StrictRedis(connection_pool=self._redis_pool)
        return self._conn

    def __getattr__(self, cmd):
        def _exec_cmd(*args, **kwargs):
            return getattr(self._conn, cmd)(*args, **kwargs)

        return _exec_cmd

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()
