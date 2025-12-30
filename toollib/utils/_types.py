from typing import Any, Protocol, TypeVar, Generic


class VFrom(Protocol):
    def get(self, key: Any, default: Any = None) -> Any:
        ...


class VConvert(Protocol):
    def __call__(self, value: Any) -> Any:
        ...


T = TypeVar('T')


class FrozenVar(Generic[T]):
    __slots__ = ()
