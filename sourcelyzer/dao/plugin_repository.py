from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
import datetime

class PluginRepository(Base):
    __tablename__ = 'sourcelyzer_plugin_repository'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String)
    last_modified = Column(DateTime, onupdate=func.now())
    created_on = Column(DateTime, default=func.now())

