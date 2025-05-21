## Bellman Tools (bellman_tools)
Python tools to upload data into SQL Server using SQL Alchemy


## Installation
 - ```pip install bellman_tools```
 - Install the requirements (SQLAlchemy version needs to be below 2.0 - working on the v1.4.39)


## Usage

### SQL Tools

To retrieve data from a SQL Server.
You need first to add connection string to the .env file in the root folder.

Example of the .env file:

```DATABASE_CONNECTION_STRING="mssql+pyodbc://user:password@server_name:1433/{db}?driver=SQL+Server"```

Then you can execute this python code :

```python
from bellman_tools import sql_tools
SQL = sql_tools.Sql(db='DB')
df = SQL.load_dataframe_from_query("SELECT TOP 1 * FROM Test")
``` 

### Upload Tools

To upload data into a SQL Server database.

```python
import pandas as pd
from bellman_tools import sql_tools, upload_tools

SQL = sql_tools.Sql(db='SAM')
UPLOAD = upload_tools.Upload(SQL)

from bellman_tools.database import Test

df = pd.DataFrame([dict(Test='Testing with Upload tools')])

UPLOAD.load_basic_df_to_db(
    df,
    SQL_Alchemy_Table=Test.Test,
)
```

