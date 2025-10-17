def map_jsontype(
        typename: str,
        is_title: bool = False,
        is_keep_integer: bool = False,
) -> str:
    """
    映射json类型

    e.g.::

        typename = "str"
        mt = utils.map_jsontype(typename)

        +++++[更多详见参数或源码]+++++

    :param typename: 类型名称
    :param is_title: 是否首字母大写
    :param is_keep_integer: 是否保留integer
    :return:
    """
    maps = {
        'NoneType': 'null',
        'None': 'null',
        'bool': 'boolean',
        'str': 'string',
        'int': 'number',
        'float': 'number',
        'list': 'array',
        'tuple': 'array',
        'dict': 'object',
    }
    if is_keep_integer:
        maps['int'] = 'integer'
    if jt := maps.get(typename):
        if is_title:
            return jt.title()
        return jt
    return typename
