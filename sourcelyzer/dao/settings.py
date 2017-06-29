from sourcelyzer.dao import Base
from sqlalchemy import Column, Integer, String

class Settings(Base):
    __tablename__ = 'sourcelyzer_settings'

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    setting_name = Column(String)
    setting_value = Column(String)

