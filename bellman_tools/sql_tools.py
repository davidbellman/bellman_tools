import time
import datetime
from typing import Any

import pandas as pd
import numpy as np
import getpass
import socket
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import text

# Load .env only from the current working directory (user's working dir).
# Best practice is to let the application load env vars; this is a convenience fallback.
_cwd_env = os.path.join(os.getcwd(), ".env")
if os.path.isfile(_cwd_env):
    load_dotenv(_cwd_env, override=False)
else:
    print(f"No .env file found in current directory: {os.getcwd()}")


class Sql:
    def __init__(
            self,
            server="default",
            db="master",
            engine=None,
            session=None,
            fast_executemany=True,
    ):
        self.server, self.db = server, db

        # Todo based on the server name, change the connection string
        DATABASE_CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")
        if not DATABASE_CONNECTION_STRING:
            raise RuntimeError(
                "Missing env var DATABASE_CONNECTION_STRING. Define it in your environment or .env"
            )

        if engine is None:
            engine = create_engine(
                DATABASE_CONNECTION_STRING.format(db=db),
                fast_executemany=fast_executemany,
            )

        self.engine = engine

        if session is None:
            Session = sessionmaker(bind=engine)
            session = Session()
            self.session = session
        else:
            self.session = session

    def load_dataframe_from_query(
            self,
            sql_query: str,
            replace_nan: bool = True
    ) -> pd.DataFrame:
        try:
            # df = pd.read_sql(text(sql_query), self.engine.connect())
            df = pd.read_sql(text(sql_query), self.engine)  # Needed in SQLAlchemy>2 version
            if replace_nan:
                df.replace({np.nan: None}, inplace=True)
                df.replace({pd.NaT: None}, inplace=True)
                return df
            else:
                return df
        except Exception as e:
            print("ERROR1348 : ", e)
            return None

    def add_to_session(self, new_entry):
        self.session.add(new_entry)

    def commit_session(self):
        try:
            self.session.commit()
        except Exception as e:
            print("ERROR1323 : Error during Session commit ", e)
            self.session.rollback()
            print("Session rollbacked")

    def execute_sql(self, sql_query):
        try:
            # Use a transactional context compatible with SQLAlchemy 1.4/2.x
            with self.engine.begin() as connection:
                connection.execute(text(sql_query))
            return True
        except Exception as e:
            print("ERROR1134 : ", e)
            print(sql_query)
            return False

    def add_to_session_and_commit(self, new_entry):
        try:
            self.session.add(new_entry)
            self.session.commit()
            print("New entry commited : ", new_entry)
        except Exception as E:
            print("ERROR1607 : ", E)
            self.session.rollback()
            print("Rollback done")

    def save_dataframe_to_sql_alchemy_table(
            self,
            df,
            SQL_Alchemy_Table,
            add_inserted_at: bool = False,
            add_inserted_by: bool = False,
            add_inserted_host: bool = False,
            object_casting: bool = False,
            insert_via_pandas: bool = False,
            insert_line_by_line: bool = False,
            debug_print_number_of_rows: int = 10,
    ):
        start = time.time()

        if df is None:
            print("Dataframe empty - No insertions")
            return

        if len(df) == 0:
            print("Dataframe empty - No insertions")
            return

        if add_inserted_at:
            # df['InsertedAt'] = datetime.datetime.now()
            df["InsertedAt"] = pd.Timestamp.now()

        if add_inserted_by:
            df["InsertedBy"] = getpass.getuser()

        if add_inserted_host:
            df["InsertedHost"] = socket.gethostname()

        df.replace({pd.NaT: None}, inplace=True)
        df.replace({np.nan: None}, inplace=True)

        try:
            # save the df into DB
            df = df.reset_index(drop=True)
            if object_casting:
                df = df.astype(object)
            df = df.where(pd.notnull(df), None)
            print("Data to commit : ", len(df))

            if insert_via_pandas:
                df.to_sql(
                    con=self.engine,
                    schema="dbo",
                    name=SQL_Alchemy_Table.__tablename__,
                    if_exists="append",
                    index=False,
                )
            elif insert_line_by_line:
                for index, row in df.iterrows():
                    row_dict = row.to_dict()
                    sql_insert = insert_sql_query(
                        table_name=SQL_Alchemy_Table.__tablename__,
                        dico_name_value=row_dict,
                    )
                    print(sql_insert)
                    self.execute_sql(sql_query=sql_insert)
            else:
                temp_dict = df.to_dict("records")
                self.session.bulk_insert_mappings(
                    SQL_Alchemy_Table,
                    temp_dict,
                )
                self.session.commit()
                print("Data commited! ", len(df))

        except Exception as e:
            print("Error : ", e)
            self.session.rollback()
            if debug_print_number_of_rows is not None and debug_print_number_of_rows > 0:
                print("Printing the top 10 rows INSERT")
                for index, row in df[:debug_print_number_of_rows].iterrows():
                    print(
                        insert_sql_query(
                            table_name=SQL_Alchemy_Table.__tablename__,
                            dico_name_value=row.to_dict(),
                        )
                    )
                print("ERROR1635 : Session rolled back ....")

        execution_time = time.time() - start
        print("Execution time : ", execution_time)
        if execution_time > 0:
            print("Speed: ", (len(df) / 1000) / execution_time, " k/s")


def update_sql_query_for_id(table_name, dico_name_value, id):
    """
    Example of dico_name_value
    dico_name_value = {
        'BbgTicker': 'HELLO US',
        'EventType': 'ER',
        'IsConfirmed': True,
        'EventDate':datetime.date(2019,5,21),
        'InsertedAt':datetime.datetime.now()
    }
    """

    res = ""
    res += "UPDATE {table_name} SET ".format(table_name=table_name)

    last_key = list(dico_name_value.keys())[-1]
    for key, val in dico_name_value.items():
        commas = "" if key == last_key else ","
        val_str = value_to_string_db(val)
        res += "{field}={value}{commas} ".format(
            field=key, value=val_str, commas=commas
        )

    res += " WHERE ID={id}".format(id=id)

    return """{x}""".format(x=res)


def insert_sql_query(table_name, dico_name_value):
    """
    Example of dico_name_value
    dico_name_value = {
        'BbgTicker': 'HELLO US',
        'EventType': 'ER',
        'IsConfirmed': True,
        'EventDate':datetime.date(2019,5,21),
        'InsertedAt':datetime.datetime.now()
    }
    """

    res = ""
    res += "INSERT INTO {table_name} (".format(table_name=table_name)

    last_key = list(dico_name_value.keys())[-1]

    # List all fields
    for key, val in dico_name_value.items():
        final = ")" if key == last_key else ","
        res += "{field}{final} ".format(field=key, final=final)

    res += " VALUES ("

    # List of values
    for key, val in dico_name_value.items():
        final = ")" if key == last_key else ","
        val_str = value_to_string_db(val)
        res += "{value}{final} ".format(value=val_str, final=final)

    return """{x}""".format(x=res)


def value_to_string_db(val):
    if type(val) is str:
        val = val.replace("'", "''")
        res = "'{val}'".format(val=val).strip()
    elif type(val) is bool:
        res = 1 if val else 0
    elif isinstance(val, datetime.datetime):
        res = "'{str_date}'".format(str_date=val.strftime("%Y-%m-%d %H:%M:%S"))
    elif isinstance(val, datetime.date):
        res = "'{str_date}'".format(str_date=val.strftime("%Y-%m-%d"))
    elif val == "":
        res = "NULL"
    elif val is None:
        res = "NULL"
    else:
        res = val
    return res


def compare_df_with_existing_and_get_only_new_rows(
        df_incoming: pd.DataFrame,
        df_existing: pd.DataFrame,
        ignored_columns=None,
        cast_to_existing_dtypes: bool = False,
) -> Any | None:
    """
    Obtain only the records which have not yet been inserted in the DB

    Args:
            df_incoming: New records to filter
            df_existing: Old records to compare
            ignored_columns: List of columns not to compare,
                default behaviour wil keep the column from df_incoming

    Returns:
            DataFrame of difference between incoming and existing records

    """

    if (
            df_existing is not None
            and df_incoming is not None
            and len(df_existing) > 0
            and len(df_incoming) > 0
    ):
        cols = df_incoming.columns.to_list()

        if ignored_columns is not None:
            cols = list(set(cols) - set(ignored_columns))

        if cast_to_existing_dtypes:
            try:
                df_incoming = df_incoming.astype(
                    df_existing[df_incoming.columns].dtypes.to_dict()
                )
            except Exception as e:
                print("Could not cast :", e)

        df_diff = df_incoming.merge(
            df_existing, indicator=True, on=cols, how="left"
        ).loc[lambda x: x["_merge"] == "left_only"]

        if ignored_columns is not None:
            df_diff = df_diff.drop(
                [col for col in ignored_columns if col in df_diff.columns],
                axis=1
            )
            df_diff = df_diff.drop(
                [
                    col + "_y"
                    for col in ignored_columns
                    if col + "_y" in df_diff.columns
                ],
                axis=1,
            )
            df_diff = df_diff.rename(
                {
                    col + "_x": col
                    for col in ignored_columns
                    if col + "_x" in df_diff.columns
                },
                axis=1,
            )

        df_diff = df_diff.drop("_merge", axis=1)

        return df_diff
    else:
        return df_incoming


def get_inserted_by():
    return getpass.getuser()


def get_inserted_host():
    return socket.gethostname()


if __name__ == "__main__":
    SQL = Sql(db='DB')
    df = SQL.load_dataframe_from_query("SELECT TOP 1 * FROM Test")
    print(df)
    pass
