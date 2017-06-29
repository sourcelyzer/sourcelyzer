from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime

class Issue(Base):
    __tablename__ = 'sourcelyzer_issues'

    issue_id = Column(Integer, primary_key=True, autoincrement=True)
    source_issue_id = Column(String)
    normalized_level = Column(String)
    true_level = Column(String)
    message = Column(Text)
    title = Column(String)
    line_number = Column(Integer)
    column_number = Column(Integer)


