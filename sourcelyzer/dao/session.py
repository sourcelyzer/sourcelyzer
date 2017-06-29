from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
import datetime

class Session(Base):
    __tablename__ = 'sourcelyzer_sessions'

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    created_on = Column(DateTime)
    expires_on = Column(DateTime)



