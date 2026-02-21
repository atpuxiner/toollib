from typing import Any, Protocol, TypeVar, Generic


class VFrom(Protocol):
    def get(self, key: Any, default: Any = None) -> Any:
        ...

    def __contains__(self, key: Any) -> bool:
        ...


class VConverter(Protocol):
    def __call__(self, value: Any) -> Any:
        ...


T = TypeVar('T')


class FrozenVar(Generic[T]):
    __slots__ = ()


class _Undefined:
    def __repr__(self):
        return "<Undefined>"


Undefined = _Undefined()
