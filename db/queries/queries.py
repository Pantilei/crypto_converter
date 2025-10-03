import pathlib

import aiosql
from aiosql.queries import Queries

queries: Queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "asyncpg")
