import os


class RedirectStd12ToNull:
    """
    重定向标准输出错误到null

    e.g.::

        with RedirectStd12ToNull():
            # 你要重定向的代码块

        # 另：取消stderr的重定向
        with RedirectStd12ToNull(is_stderr=False):
            # 你要重定向的代码块

        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, is_stderr: bool = True):
        """
        初始化
        :param is_stderr: 是否重定向stderr
        """
        self.is_stderr = is_stderr
        self.null_1fd = os.open(os.devnull, os.O_RDWR)
        self.save_1fd = os.dup(1)
        if self.is_stderr is True:
            self.null_2fd = os.open(os.devnull, os.O_RDWR)
            self.save_2fd = os.dup(2)

    def __enter__(self):
        os.dup2(self.null_1fd, 1)
        if self.is_stderr is True:
            os.dup2(self.null_2fd, 2)

    def __exit__(self, *_):
        os.dup2(self.save_1fd, 1)
        os.close(self.null_1fd)
        if self.is_stderr is True:
            os.dup2(self.save_2fd, 2)
            os.close(self.null_2fd)
