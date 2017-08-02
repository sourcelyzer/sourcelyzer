from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
import datetime

class Plugin(Base):
    __tablename__ = 'sourcelyzer_plugin'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer)
    key = Column(String)
    group = Column(String)
    name = Column(String)
    version = Column(String)
    description = Column(String)
    author = Column(String)
    created_on = Column(DateTime, default=func.now())
    last_modified = Column(DateTime, onupdate=func.now())
    installed = Column(Boolean)
    enabled = Column(Boolean)
