from functools import reduce
from typing import Callable, Iterable


def B(f: Callable, g: Callable) -> Callable:
    def f_after_g(*args, **kwargs):
        return f(g(*args, **kwargs))

    return f_after_g


def compose(fns: Iterable[Callable]) -> Callable:
    return reduce(B, fns)
