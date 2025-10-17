from threading import Lock


class Singleton(type):
    """
    单例模式

    e.g.::

        # 使类A变为单例模式
        class A(metaclass=Singleton):
            pass

        +++++[更多详见参数或源码]+++++
    """

    _instances = {}
    _locks = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            if cls not in cls._locks:
                cls._locks[cls] = Lock()
            with cls._locks[cls]:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
