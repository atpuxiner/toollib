"""
@author axiner
@version v1.0.0
@created 2022/2/27 11:46
@abstract 加密
@description
@history
"""
import typing as t
from pathlib import Path

from toollib.validator import choicer

__all__ = [
    'cmd5',
    'curl',
    'cbase64',
    'cdes',
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
    _obj = md5()
    if is_file is True:
        with open(obj, 'rb') as f:
            while True:
                b = f.read(10240)
                if not b:
                    break
                _obj.update(b)
    else:
        _obj.update(obj.encode('utf8'))
    if salt:
        _obj.update(salt.encode('utf8'))
    return _obj.hexdigest()


def curl(obj, mode: int = 1):
    """
    url加密与解密
    :param obj: 对象
    :param mode: 模式（1-加密；2-解密）
    :return:
    """
    from urllib import parse
    mode = choicer(mode, [1, 2], 'mode')
    if mode == 1:
        _obj = parse.quote(obj)
    else:
        _obj = parse.unquote(obj)
    return _obj


def cbase64(obj, mode: int = 1, to_file: t.Union[str, Path] = None, altchars=None, validate=False):
    """
    base64加密与解密
    :param obj: 对象
    :param mode: 模式（1-加密；2-解密）
    :param to_file: 输出指定文件（针对obj为文件对象）
    :param altchars: alt chars
    :param validate:
    :return:
    """
    import base64
    mode = choicer(mode, [1, 2], 'mode')
    if to_file:
        with open(obj, 'rb') as f, open(to_file, 'wb') as f2:
            for line in f.readlines():
                if mode == 1:
                    f2.write(base64.b64encode(line, altchars))
                    f2.write(b'\n')
                else:
                    f2.write(base64.b64decode(line, altchars))
        return to_file
    else:
        if mode == 1:
            _obj = base64.b64encode(obj, altchars)
        else:
            _obj = base64.b64decode(obj, altchars, validate)
        return _obj


def cdes(obj, deskey='12345678', desiv='abcdefgh', mode: int = 1,
         to_file: t.Union[str, Path] = None,
         desmode='CBC', despadmode='PAD_PKCS5'):
    """
    des加密与解密（des mode: ECB or CBC）
    :param obj: 对象
    :param deskey: des key（8 bytes）
    :param desiv: des iv向量（8 bytes）
    :param mode: 模式（1-加密；2-解密）
    :param to_file: 输出指定文件（针对obj为文件对象）
    :param desmode: des mode (ECB or CBC, 默认为 CBC)
    :param despadmode: despad mode (PAD_NORMAL or PAD_PKCS5, 默认为 PAD_PKCS5)
    :return:
    """
    import base64
    try:
        import pyDes
    except ImportError:
        raise
    desmode = choicer(desmode, ['ECB', 'CBC'], 'desmod')
    despadmode = choicer(despadmode, ['PAD_NORMAL', 'PAD_PKCS5'], 'despadmode')
    despad = None
    desmode = {'ECB': pyDes.ECB, 'CBC': pyDes.CBC}.get(desmode)
    despadmode = {'PAD_NORMAL': pyDes.PAD_NORMAL, 'PAD_PKCS5': pyDes.PAD_NORMAL}.get(despadmode)
    if despadmode == pyDes.PAD_NORMAL:
        despad = 'z'
    _des = pyDes.des(deskey, desmode, desiv, pad=despad, padmode=despadmode)
    if to_file:
        with open(obj, 'rb') as f, open(to_file, 'wb') as f2:
            for line in f.readlines():
                if mode == 1:
                    f2.write(base64.b64encode(_des.encrypt(line)))
                    f2.write(b'\n')
                else:
                    f2.write(_des.decrypt(base64.b64decode(line)))
        return to_file
    else:
        if mode == 1:
            _obj = base64.b64encode(_des.encrypt(obj))
        else:
            _obj = _des.decrypt(base64.b64decode(obj))
        return _obj
