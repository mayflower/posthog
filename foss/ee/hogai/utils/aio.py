"""Run an async generator from synchronous code, one item at a time.

Core uses this to serve streaming responses under WSGI, so it has to work in the FOSS build.
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from typing import TypeVar

T = TypeVar("T")


def async_to_sync(factory: Callable[[], AsyncIterator[T]]) -> Iterator[T]:
    loop = asyncio.new_event_loop()
    try:
        aiter = factory()
        while True:
            try:
                yield loop.run_until_complete(aiter.__anext__())
            except StopAsyncIteration:
                return
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
