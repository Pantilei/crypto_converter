import inspect
from typing import TYPE_CHECKING, Any, ClassVar, TypeIs

import asyncpg
from loguru import logger


class BaseRepo:
    if TYPE_CHECKING:
        pool: asyncpg.Pool
    
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name


class DBManager:
    pool: ClassVar[asyncpg.Pool]
    _repos: ClassVar[dict[str, BaseRepo]] = {}

    def __init_subclass__(cls) -> None:
        def __is_base_repo(cls_mem: Any) -> TypeIs[BaseRepo]:
            return isinstance(cls_mem, BaseRepo)

        for name, inst in inspect.getmembers(cls, __is_base_repo):
            cls._repos[name] = inst


    @classmethod
    async def connect(cls, dsn: str) -> None:
        if cls == DBManager:
            raise RuntimeError("Cannot connect from this level.")
    
        if getattr(cls, "pool", None) is not None:
            raise RuntimeError("Already connected!")

        cls.pool = await asyncpg.create_pool(dsn=dsn)
        for name, repo in cls._repos.items():
            logger.info(f"Repo {name} ready.")
            repo.pool = cls.pool
    
    @classmethod
    async def disconnect(cls) -> None:
        if cls == DBManager:
            raise RuntimeError("Cannot disconnect from this level.")
    
        if getattr(cls, "pool") is None:
            raise RuntimeError("Connect first!")
        await cls.pool.close()
