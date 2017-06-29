from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
import datetime

class Project(Base):
    __tablename__ = 'sourcelyzer_projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    last_modified = Column(DateTime, onupdate=func.now())
    created_on = Column(DateTime, default=func.now())
    key = Column(String, unique=True)
 
