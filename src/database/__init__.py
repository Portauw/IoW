import sqlalchemy as db
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()
from .movement import Movement
from .platform_sync import PlatformSync
from sqlalchemy.sql import exists
from typing import List
from os import path
from src.log import logger
from config import cfg


class DbManager:
    def __init__(self):
        self.engine = create_engine(cfg.full_sqlite_path, connect_args={'timeout': 60})

        if not path.exists(f"{cfg.root_dir}/{cfg.sqlitePath}") or \
                cfg.full_sqlite_path == "sqlite://" or \
                cfg.full_sqlite_path == "sqlite:///:memory:":
            # 2 - generate database schema
            logger.info(f"[DB] DB non existent : creating @ {cfg.full_sqlite_path}")
            Base.metadata.create_all(bind=self.engine)

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def close(self):
        self.Session.close()
        self.engine.dispose()

    def get_engine(self):
        return self.engine

    def get_session(self):
        return self.Session()

    def get_entered(self):
        """ Get number of people entered that have not been synced yet """
        s = self.get_session()
        n_in = s.query(func.count()).filter(Movement.entered == True).scalar()
        return n_in

    def get_left(self):
        """ Get number of people left that have not been synced yet """
        s = self.get_session()
        n_out = s.query(func.count()).filter(Movement.entered == False).scalar()
        return n_out

    def stuff_single_entry(self, entered: bool):
        """ Add sample to local DB with 1 entered or left"""
        s = self.get_session()

        ids_sample = Movement()
        ids_sample.entered = entered

        s.add(ids_sample)
        s.commit()

    def get_unsynced(self):
        """
        Get all records that exist in the Movemenbt table, but not in the PlatformSync table
        :return: List[records]
        """

        s = self.get_session()

        unsynced_data = s.query(Movement).filter(
            ~exists().where(Movement.id == PlatformSync.idm)) \
            .order_by(Movement.timestamp.asc()).all()

        return unsynced_data

    def update_synced(self, idms: List[int]):
        """
        Add the Movement ID's to PlatformSync table
        :param idms: List of ID's to add
        :return: None
        """

        s = self.get_session()

        for id in idms:
            tmp = PlatformSync()
            tmp.idm = id
            s.add(tmp)

        s.commit()
