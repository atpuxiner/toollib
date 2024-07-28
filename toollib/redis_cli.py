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

        # 1) 单个连接使用
        r = RedisCli(host='127.0.0.1')

        # 或，使用with
        with RedisCli(host='127.0.0.1') as r:
            pass

        #2）以连接池的方式

        # 2.1）创建连接池
        redis_cli = RedisCli(host='127.0.0.1', max_connections=100)
        redis_conn = redis_cli.connection

        # 2.2）调用连接（每次获取连接池中连接）
        r = redis_conn()

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
        self.__conn = redis.StrictRedis(connection_pool=self._redis_pool)

    def connection(self):
        """
        创建连接
        :return:
        """
        self.__conn = redis.StrictRedis(connection_pool=self._redis_pool)
        return self.__conn

    def __getattr__(self, cmd):
        def exec_cmd(*args, **kwargs):
            return getattr(self.__conn, cmd)(*args, **kwargs)
        return exec_cmd

    def __enter__(self):
        return self.__conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__conn.close()
