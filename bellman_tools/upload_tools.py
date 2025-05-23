import datetime
from typing import List, Dict
import os

import pandas as pd
import numpy as np

from bellman_tools import sql_tools

class Upload:
	def __init__(self,sql: sql_tools.Sql):
		self.Sql = sql

	def load_basic_df_to_db(
			self,
			df_incoming: pd.DataFrame,
			SQL_Alchemy_Table,
			mapping_columns_to_db: dict = None,
			check_with_existing: bool = False,
			file_path: str = None,
			extra_col_to_ignore: List[str] = None,
			str_existing_query: str = None,
			insert_via_pandas: bool = False,
			insert_line_by_line: bool = False,
			col_precision: Dict[str, int] = None,
			cast_to_existing_dtypes: bool = True,
			df_existing: pd.DataFrame = None,
			replace_nan=False,
			add_inserted_at: bool = True,
			add_inserted_by: bool = True,
			add_inserted_host: bool = True,
	):
		"""Args:
		- col_precision: a dict containing rounding precision for columns for
		when you do the comparison. This helps avoid
		overflow issues causing false duplicates being inserted into DB
		"""

		ignored_columns = ["ID", "InsertedAt", "InsertedBy", "InsertedHost"]

		if extra_col_to_ignore:
			ignored_columns.extend(extra_col_to_ignore)

		if replace_nan:
			df_incoming = df_incoming.replace({np.nan: None})

		if mapping_columns_to_db is not None:
			df_incoming.rename(columns=mapping_columns_to_db, inplace=True)

		if check_with_existing is True or str_existing_query is not None:
			if (
					str_existing_query is None
					and df_existing is None
					and check_with_existing is True
			):
				str_existing_query = f"SELECT * FROM " + SQL_Alchemy_Table.__tablename__

			if str_existing_query is not None:
				df_existing = self.Sql.load_dataframe_from_query(
					sql_query=str_existing_query,
					replace_nan=replace_nan
				)

		if df_existing is not None and col_precision is not None:
			df_incoming = df_incoming.round(col_precision)
			df_existing = df_existing.round(col_precision)

		df_diff = sql_tools.compare_df_with_existing_and_get_only_new_rows(
			df_incoming=df_incoming,
			df_existing=df_existing,
			ignored_columns=ignored_columns,
			cast_to_existing_dtypes=cast_to_existing_dtypes,
		)

		if len(df_diff) > 0:
			print(f"Adding data for {SQL_Alchemy_Table.__tablename__}")

			if file_path is not None:
				df_diff["FilePath"] = file_path

			df_diff = df_diff.replace({np.nan: None})

			self.Sql.save_dataframe_to_sql_alchemy_table(
				df=df_diff,
				SQL_Alchemy_Table=SQL_Alchemy_Table,
				object_casting=True,
				add_inserted_at=add_inserted_at,
				add_inserted_by=add_inserted_by,
				add_inserted_host=add_inserted_host,
				insert_via_pandas=insert_via_pandas,
				insert_line_by_line=insert_line_by_line,
			)
			return df_diff
		else:
			print("No data to insert")


if __name__ == '__main__':
	SQL = sql_tools.Sql(db='SAM')
	UPLOAD = Upload(sql=SQL)

	from bellman_tools.database import Test

	df = pd.DataFrame([dict(Test='Testing with Python #2')])

	UPLOAD.load_basic_df_to_db(
		df,
		SQL_Alchemy_Table=Test.Test,
	)