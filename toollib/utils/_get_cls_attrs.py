from typing import get_type_hints


def get_cls_attrs(cls, is_keep_parent: bool = False) -> dict:
    """
    获取类属性

    e.g.::

        # 获取类属性
        class A:

            def foo(self):
                cls_attrs = get_cls_attrs(A)

        +++++[更多详见参数或源码]+++++
    """
    if is_keep_parent:
        type_hints = get_type_hints(cls.__bases__[0]) if cls.__bases__ else {}
    else:
        type_hints = get_type_hints(cls)
        if cls.__bases__:
            parent_type_hints = {}
            for base in cls.__bases__:
                parent_type_hints.update(get_type_hints(base))
            type_hints = {k: v for k, v in type_hints.items() if k not in parent_type_hints}
    attrs = {}
    for attr_name, attr_type in type_hints.items():
        attr_value = getattr(cls, attr_name, None)
        attrs[attr_name] = (attr_type, attr_value)
    return attrs
