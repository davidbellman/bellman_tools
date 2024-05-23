from bellman_tools import sql_tools
SQL = sql_tools.Sql(db='SAM')

table_name = 'Test'

from sqlalchemy import MetaData
meta = MetaData(SQL.engine)
meta.reflect(only=[table_name])
table = meta.tables[table_name]

all_fields = ""

for column in table.columns:
	print(column.name, column.type, column.nullable, column.primary_key)
	type_str = str(column.type).split('(')[0].title()

	if type_str == 'Varchar' : type_str = 'String'
	if type_str == 'Bigint' : type_str = 'BigInteger'
	if type_str == 'Bit' : type_str = 'Boolean'
	if type_str == 'Datetime' : type_str = 'DateTime'
	if column.name == 'ID' : continue

	all_fields += f"\t{column.name} = Column({type_str})\n"


str_output = f"""
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

from database import db_template

DBTemplate = db_template.db_template


class {table_name}(Base, DBTemplate):
	__tablename__ = '{table_name}'
	ID = Column(Integer, primary_key=True)
{all_fields}"""

print(str_output)
