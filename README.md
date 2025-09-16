## Bellman Tools (bellman_tools)
Utilities for reading from and writing to Microsoft SQL Server using SQLAlchemy and pandas.

Supports Python 3.10+ and SQLAlchemy 2.x.

## Installation

```bash
pip install bellman-tools
```

### Prerequisites

- Microsoft ODBC Driver for SQL Server (e.g. "ODBC Driver 18 for SQL Server")
- `pyodbc` installed (pulled in automatically)

## Configure the connection

Set an environment variable named `DATABASE_CONNECTION_STRING`. The string must include a `{db}` placeholder that will be replaced by the database name you pass to `Sql(db=...)`.

Example `.env` (place it in your current working directory):

```bash
DATABASE_CONNECTION_STRING="mssql+pyodbc://username:password@server-host:1433/{db}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

If your machine provides an older driver name, you can also use:

```bash
DATABASE_CONNECTION_STRING="mssql+pyodbc://username:password@server-host:1433/{db}?driver=SQL+Server"
```

#### Notes on environment loading

- `bellman_tools.sql_tools` looks for a `.env` file only in your current working directory when it is imported. If not found, it prints the directory and continues.
- Prefer setting environment variables via your shell or secrets manager. The `.env` support is a convenience fallback.

## Quickstart

### Query data

```python
from bellman_tools import sql_tools

SQL = sql_tools.Sql(db="DB")
df = SQL.load_dataframe_from_query("SELECT TOP 1 * FROM Test")
```

### Upload data

Define a SQLAlchemy model for your target table (one-time setup):

Tip: You can generate model boilerplate from an existing table:

```python
print(UPLOAD.create_schema(table_name="YourTable"))
```

Then create a file in your project, e.g. `database\Test.py`:

```python
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from bellman_tools.database.db_template import db_template as DBTemplate

Base = declarative_base()

class Test(Base, DBTemplate):
    __tablename__ = "Test"
    __table_args__ = {"schema": "dbo"}
    ID = Column(Integer, primary_key=True)
    Test = Column(String)
```

Insert a DataFrame, optionally avoiding duplicates against existing rows:

```python
import pandas as pd
from bellman_tools import sql_tools, upload_tools

SQL = sql_tools.Sql(db="SAM")
UPLOAD = upload_tools.Upload(SQL)

df = pd.DataFrame([{"Test": "Testing with Upload tools"}])

UPLOAD.load_basic_df_to_db(
    df_incoming=df,
    SQL_Alchemy_Table=Test,
    check_with_existing=True,  # optional: compare with existing rows before insert
)
```



## DataFrame comparison utility

Use `compare_df_with_existing_and_get_only_new_rows` to filter only new rows by comparing two DataFrames on shared columns.

```python
import pandas as pd
from bellman_tools import sql_tools

df_incoming = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})
df_existing = pd.DataFrame({"id": [1], "value": ["a"]})

df_diff = sql_tools.compare_df_with_existing_and_get_only_new_rows(
    df_incoming=df_incoming,
    df_existing=df_existing,
)
# df_diff contains the row id=2, value="b"
```

Key options:

- **ignored_columns**: columns to exclude from the comparison. Defaults to `ID`, `InsertedAt`, `InsertedBy`, `InsertedHost` in upload workflows. You can pass your own list.
- **cast_to_existing_dtypes**: when `True`, casts `df_incoming` to the dtypes of `df_existing` for compared columns to avoid false mismatches.

## API at a glance

- **Sql**
  - `Sql(db, server="default", fast_executemany=True, ...)`
  - `load_dataframe_from_query(sql_query, replace_nan=True) -> pandas.DataFrame`
  - `execute_sql(sql_query) -> bool`

- **Upload**
  - `Upload(sql: Sql)`
  - `load_basic_df_to_db(df_incoming, SQL_Alchemy_Table, mapping_columns_to_db=None, check_with_existing=False, str_existing_query=None, col_precision=None, cast_to_existing_dtypes=True, insert_via_pandas=False, insert_line_by_line=False, add_inserted_at=True, add_inserted_by=True, add_inserted_host=True, ...)`
  - `create_schema(table_name) -> str` (returns Python class boilerplate for a table)

## Troubleshooting

- **"No .env file found in current directory"**: Set `DATABASE_CONNECTION_STRING` in your environment or create a `.env` in your current working directory.
- **ODBC driver errors**: Install the Microsoft ODBC Driver for SQL Server and ensure the `driver=` value in your connection string matches the installed driver name.
- **SQLAlchemy 2.x**: This package is compatible with SQLAlchemy 2.x; queries use `sqlalchemy.text` under the hood.

## Links

- Source: `https://github.com/davidbellman/bellman_tools`


