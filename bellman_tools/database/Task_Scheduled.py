from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Time, Date, BigInteger

class Task_Scheduled(Base):
	__tablename__ = 'Task_Scheduled'
	__table_args__ = {'schema': 'dbo'}
	ID = Column(Integer, primary_key=True)
	ScriptName = Column(String)
	ScriptFolder = Column(String)
	RunBy = Column(String)
	RunHost = Column(String)
	NextRun = Column(DateTime)
	HeartbeatID = Column(String)
	InsertedAt = Column(DateTime)
	InsertedBy = Column(String)
	InsertedHost = Column(String)