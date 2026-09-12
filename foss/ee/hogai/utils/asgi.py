"""Expose a synchronous iterable as an async iterator without blocking the event loop."""

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar, cast

from asgiref.sync import sync_to_async

T = TypeVar("T")
_DONE = object()


class SyncIterableToAsync(Generic[T]):
    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator: Iterator[T] = iter(iterable)

    def __aiter__(self) -> "SyncIterableToAsync[T]":
        return self

    async def __anext__(self) -> T:
        item = await sync_to_async(next, thread_sensitive=False)(self._iterator, _DONE)
        if item is _DONE:
            raise StopAsyncIteration
        return cast(T, item)
