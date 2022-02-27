"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:46
@abstract
@description
@history
"""

__all__ = [
    'cmd5',
]


def cmd5(obj, salt: str = '', is_file: bool = False):
    """
    md5加密
    :param obj: 对象
    :param salt: 加盐
    :param is_file: 是否针对文件对象
    :return:
    """
    from hashlib import md5
    obj_md5 = md5()
    if is_file is True:
        with open(obj, 'rb') as f:
            while True:
                b = f.read(10240)
                if not b:
                    break
                obj_md5.update(b)
    else:
        obj_md5.update(obj.encode('utf8'))
    if salt:
        obj_md5.update(salt.encode('utf8'))
    return obj_md5.hexdigest()
