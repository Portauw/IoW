from sqlalchemy import Column, Integer, DateTime
from src.database import Base
from datetime import datetime
import time


def get_now():
    return int(time.time())


class PlatformSync(Base):
    __tablename__ = "platform_sync"
    id = Column(Integer(), primary_key=True, autoincrement=True, nullable=False, unique=True)
    idm = Column(Integer(), nullable=False)
    synced_timestamp = Column(Integer(), nullable=False, default=get_now, onupdate=get_now)

    def update(self, changes):
        for key, val in changes.items():
            setattr(self, key, val)
        return
