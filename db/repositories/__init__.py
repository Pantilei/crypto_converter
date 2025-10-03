from db.repositories.base import DBManager
from db.repositories.candles_1s.repo import Candles1sRepo


class DB(DBManager):
    candles_1s = Candles1sRepo("candles_1s")
