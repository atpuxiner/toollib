## toollib.crypto

@author axiner
@version v1.0.0
@created 2022/2/27 11:46
@abstract 加密
@description
@history

## cmd5
md5加密
    使用示例：
    ```py
        # 1）针对字符
        obj = 'this is toollib'
        cobj = crypto.cmd5(obj)
        # 2）针对文件
        obj = 'D:/tmp/t.txt'
        cobj = crypto.cmd5(obj, is_file=True)
        # ret: 返回obj的md5
        +++++[更多详见参数或源码]+++++
    :param obj: 对象
    :param is_file: 是否针对文件对象
    :param saltstr: 加盐字符串
    :return:
    ```

## curl