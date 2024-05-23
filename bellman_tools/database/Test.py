from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
from sqlalchemy import (
	Column,
	Integer,
	String,
	DateTime,
	Float,
	Boolean,
	Time,
	Date,
	BigInteger,
)

from bellman_tools.database import db_template

DBTemplate = db_template.db_template


class Test(Base, DBTemplate):
	__tablename__ = 'Test'
	ID = Column(Integer, primary_key=True)
	Test = Column(String)
	InsertedAt = Column(DateTime)
	InsertedBy = Column(String)
	InsertedHost = Column(String)