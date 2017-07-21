from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
import datetime

class ScmCommit(Base):
    __tablename__ = 'sourcelyzer_scm_commit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_id = Column(Integer)
    author = Column(String)
    message = Column(Text)
    created_on = Column(DateTime, default=func.now())
    commit_date = Column(DateTime)

