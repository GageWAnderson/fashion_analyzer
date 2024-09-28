__all__ = ["amap", "ajoin"]

from functools import partial
from typing import AsyncGenerator, AsyncIterable, Callable


async def amap(func: Callable, async_iterable: AsyncIterable) -> AsyncGenerator:
    async for value in async_iterable:
        yield func(value)


async def ajoin(by: str, items: AsyncIterable[str]) -> AsyncGenerator[str, None]:
    yield await anext(_items := aiter(items), "")
    async for _item in amap(partial("{}{}".format, by), _items):
        yield _item
