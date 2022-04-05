import time
import sqlalchemy as db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from .movement import Movement
from .platform_sync import PlatformSync
from threading import Thread, Event
from src.log import logger

CLEAN_INTERVAL = 1


class DataBaseCleaner(Thread):
    def __init__(self, stop_event: Event, sql_uri: str, interval: float = CLEAN_INTERVAL):
        self._stop_event = stop_event
        self._interval = interval
        self.sql_uri = sql_uri
        super().__init__()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                engine = db.create_engine(self.sql_uri, connect_args={'timeout': 60})
                session_factory = sessionmaker(bind=engine)
                session = scoped_session(session_factory)
                query = text(
                    "SELECT ids_id FROM platform_sync "
                    "INNER JOIN intra_day_second_data "
                    "ON platform_sync.ids_id = intra_day_second_data.id "
                    "AND intra_day_second_data.is_synced = 1")
                ids_to_delete = [id[0] for id in session().execute(query).fetchall()]
                del_ids_intra = Movement.__table__.delete().where(Movement.id.in_(ids_to_delete))
                del_ids_platform = PlatformSync.__table__.delete().where(PlatformSync.ids_id.in_(ids_to_delete))
                session().execute(del_ids_intra)
                session().execute(del_ids_platform)
                session().commit()
                session().close()
            except SQLAlchemyError as e:
                logger.error(f"[DBCLEAN] Received SQLAlchemyError {e}")

            time.sleep(self._interval)
        logger.info(f"[DBCLEAN] stopping thread")
