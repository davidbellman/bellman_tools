from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, Date,Float, Boolean, DateTime

class Log_Task_Scheduler(Base):

	__tablename__ = 'Log_Task_Scheduler'
	__table_args__ = {'schema': 'dbo'}
	ID = Column(Integer, primary_key=True)
	ScriptFile = Column(String)
	Status = Column(String)
	SessionID = Column(String)
	IsProd = Column(Boolean)
	TraceID = Column(String)
	HeartbeatID = Column(String)
	InsertedAt = Column(DateTime)
	InsertedBy = Column(String)
	InsertedHost = Column(String)