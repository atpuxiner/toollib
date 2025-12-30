from typing import get_type_hints


def get_cls_attrs(cls) -> dict:
    """
    获取类属性

    e.g.::

        # 获取类属性
        class B(A):

            def foo(self):
                cls_attrs = get_cls_attrs(self.__class__)  # 获取包含父类的属性
                cls_attrs2 = get_cls_attrs(self)  # 获取不包含父类的属性

        +++++[更多详见参数或源码]+++++
    """
    attrs = {}
    for attr_name, attr_type in get_type_hints(cls).items():
        attr_value = getattr(cls, attr_name, None)
        attrs[attr_name] = (attr_type, attr_value)
    return attrs
