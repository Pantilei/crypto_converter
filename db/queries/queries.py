import pathlib
from typing import TYPE_CHECKING, Any

import aiosql
from aiosql.queries import Queries as _Queries

if TYPE_CHECKING:
    from collections.abc import Callable
    class Queries(_Queries):
        def __getattribute__(self, name: str) -> Callable[..., Any]:
            return super().__getattribute__(name)
else:
    Queries = _Queries

queries: Queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "asyncpg")  # type: ignore
