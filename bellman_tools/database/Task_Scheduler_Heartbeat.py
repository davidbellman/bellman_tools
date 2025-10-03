from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Time, Date, BigInteger

from database import db_template

DBTemplate = db_template.db_template


class Task_Scheduler_Heartbeat(Base, DBTemplate):
	__tablename__ = 'Task_Scheduler_Heartbeat'
	__table_args__ = {'schema': 'dbo'}
	ID = Column(Integer, primary_key=True)
	IsProd = Column(Boolean)
	SessionID = Column(String)
	InsertedAt = Column(DateTime)
	InsertedBy = Column(String)
	InsertedHost = Column(String)