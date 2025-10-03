from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Time, Date, BigInteger

from database import db_template

DBTemplate = db_template.db_template


class Task_Scheduled(Base, DBTemplate):
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