"""
@author axiner
@version v1.0.0
@created 2022/10/28 14:23
@abstract redis
@description
@history
"""
try:
    from redis import Redis, ConnectionPool
except ImportError:
    raise

__all__ = ['RedisClient']


class RedisClient:
    """
    redis客户端

    e.g.::

        # 创建
        redis_client = RedisClient(host='127.0.0.1', max_connections=100)

        # 使用方式1：标准用法（推荐）
        r = redis_client.connection()
        print(r.get("name"))
        print(r.get("age"))
        r.close()

        # 使用方式2：代理调用-每次创建新连接（不推荐）
        print(redis_client.get("name"))
        print(redis_client.get("age"))

        # 使用方式3：上下文管理器（推荐）
        with redis_client.connection() as r:
            print(r.get("name"))

        # 使用方式4：上下文管理器（简洁写法）
        with redis_client as r:
            print(r.get("name"))

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
        self._redis_pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            **kwargs,
        )

    def connection(self) -> Redis:
        """
        创建连接
        :return:
        """
        return Redis(connection_pool=self._redis_pool)

    def __getattr__(self, cmd):
        def _exec_cmd(*args, **kwargs):
            with self.connection() as conn:
                return getattr(conn, cmd)(*args, **kwargs)

        return _exec_cmd

    def __enter__(self):
        return self.connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
