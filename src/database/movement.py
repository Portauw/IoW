from sqlalchemy import Column, Integer, Boolean, DateTime
from src.database import Base
from datetime import datetime
import time


def get_now():
    return int(time.time())


class Movement(Base):
    __tablename__ = "movement"
    id = Column(Integer(), primary_key=True)
    timestamp = Column(Integer(), nullable=False, default=get_now)
    entered = Column(Boolean(), nullable=False, default=False)  # entered or left

    def update(self, changes):
        for key, val in changes.items():
            setattr(self, key, val)
        return

