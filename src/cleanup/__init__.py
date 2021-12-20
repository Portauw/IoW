import time
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

from src.database import DbManager

Base = declarative_base()
from src.database.movement import Movement
from src.database.platform_sync import PlatformSync
from threading import Thread, Event
from src.log import logger
from src.base import EdgiseBase
from multiprocessing import Queue

CLEAN_INTERVAL = 60


class DataBaseCleaner(Thread, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, interval: float = CLEAN_INTERVAL):
        self._stop_event = stop_event
        self._interval = interval
        self._db_manager = DbManager()
        Thread.__init__(self)
        EdgiseBase.__init__(self, name="DBCLEAN", logging_q=logging_q)

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                query = text(
                    "SELECT idm FROM platform_sync "
                    "INNER JOIN movement "
                    "ON platform_sync.idm = movement.id")
                ids_to_delete = [id[0] for id in self._db_manager.Session().execute(query).fetchall()]
                del_ids_movement = Movement.__table__.delete().where(Movement.id.in_(ids_to_delete))
                del_ids_platform = PlatformSync.__table__.delete().where(PlatformSync.idm.in_(ids_to_delete))
                self._db_manager.Session().execute(del_ids_movement)
                self._db_manager.Session().execute(del_ids_platform)
                self._db_manager.Session().commit()
                self._db_manager.Session().close()
                self.info(f" No Error, database cleaned")
            except SQLAlchemyError as e:
                self.error(f"Received SQLAlchemyError {e}")

            time.sleep(self._interval)
