from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Time, Date, BigInteger

from database import db_template

DBTemplate = db_template.db_template

class Task_Scheduler(Base, DBTemplate):
	__tablename__ = 'Task_Scheduler'
	__table_args__ = {'schema': 'dbo'}
	ID = Column(Integer, primary_key=True)
	Enable = Column(Boolean)
	RunBy = Column(String)
	ScriptName = Column(String)
	ScriptFolder = Column(String)
	Every = Column(String)
	AtTime = Column(String)
	Ressource = Column(String)
	ToRunAsap = Column(Boolean)
	Comment = Column(String)
	RunHost = Column(String)
	InsertedAt = Column(DateTime)
	InsertedBy = Column(String)
	InsertedHost = Column(String)
