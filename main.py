from copy import deepcopy
import os, json, gc
import datetime, time
import sys
from datetime import date
import pandas as pd
import yfinance as yf
import pyodbc
import markdown
from flask import Flask, Response, request

gc.enable()

app = Flask(__name__)

conn_string = os.environ.get("AZURE_CONN_STRING")

# cloud run burps when there is a deprecation warning
import warnings
warnings.filterwarnings("ignore")

def connect_db():
    # Construct connection string
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor() 
    return cursor

def list_sp500():
    # There are 2 tables on the Wikipedia page
    # we want the first table, return the dataframe

    payload=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    first_table = payload[0]
    second_table = payload[1]

    df_sp500 = first_table.convert_dtypes()
    return df_sp500

def load_from_df(sql_table_name, data: pd.DataFrame):
    '''Loads data to SQL server from dataframe
    '''
    if data.shape[0] ==0: return f"no data in df to load"
    df2 = data.copy(deep=True)
    df2 = df2.fillna('0')

    # create cursor and set fast execute property
    cursor = connect_db()
    cursor.fast_executemany = True

    # get list of sql columns, replace the spaces, used for insert stmnt
    sql_cols_list_qry = f'''select STRING_AGG(COLUMN_NAME,',') col_list
            from  information_schema.columns
            where table_name='{sql_table_name}'; '''
    cursor.execute(sql_cols_list_qry)
    row = cursor.fetchone()
    col_list = str(row[0])
    col_list = col_list.split(",")
    print('  col_list:' + str(col_list))
    print('  df columns:', df2.columns.to_list())

    # select columns from dataframe that are in the sql table
    common_cols = set(col_list) & set(df2.columns.to_list())
    print('  COMMON COLS:', list(common_cols))
    col_count = len(common_cols)
    df2 = df2[list(common_cols)]
    print('   First Row of Dataframe:', dict(df2.iloc[0]))

    # vals is list of question marks for each column for insert stmnt
    vals = ('?,' *(col_count -1) ) + '?'
    col_list = str(common_cols).replace("'",'"')
    col_list = col_list.replace('{','').replace('}','')
    insert_tbl_stmt = f"INSERT INTO {sql_table_name} ({col_list}) values({vals})"
    print("   insert statement:", insert_tbl_stmt)

    # insert rows
    try:
        cursor.executemany(insert_tbl_stmt, df2.values.tolist())
        print(f'   {len(df2)} rows inserted into {sql_table_name} table', datetime.datetime.now())
    except BaseException as err:
        print(f"   Unexpected {err}, {type(err)} in load_from_df")
        print(f"   Error on df values", str(df2.head(1)))
    finally:
        cursor.commit()
        cursor.close()
        del df2
    gc.collect()

    return f'Completed loading {sql_table_name} ' + str(datetime.datetime.now())

def merge_price_history(where_clause):
    '''copies data from tmp table to main table, only if not already present
    '''
    # create cursor and set fast execute property
    cursor = connect_db()

    # insert all the rows from tmp table that are not in main table.
    qry = f'''INSERT [dbo].[price_history]
        SELECT price_history_tmp.*
        FROM [dbo].[price_history_tmp] price_history_tmp
        LEFT OUTER JOIN [dbo].[price_history] ph
            ON price_history_tmp.ticker=ph.ticker and price_history_tmp.[Datetime]=ph.[Datetime] 
        {where_clause} and ph.ticker is null and price_history_tmp.Volume>0'''
    print('  merge_price_history query: ', qry)
    cursor.execute(qry)
    rowcount = cursor.rowcount
    cursor.commit()
    cursor.close()

    print(f' {rowcount} rows inserted to price_history')

def delete_table(sql_table_name, where_clause):
    '''deletes rows from a table using supplied WHERE clause
    '''
    # create cursor, execute the stmnt
    cursor = connect_db()
    qry = f'''DELETE {sql_table_name} {where_clause} '''
    cursor.execute(qry)
    rowcount = cursor.rowcount
    cursor.commit()
    cursor.close()

    print(f' {rowcount} rows deleted from {sql_table_name}:')

def dump_table_to_stream(table='INFORMATION_SCHEMA.COLUMNS', where='WHERE TRUE', format='csv'):
    '''returns all data in table with optional where clause
    '''
    print( table, where, format)
    # create cursor, execute the stmnt
    conn = pyodbc.connect(conn_string)
    qry = f'''select * FROM {table} {where} '''
    sql_query = pd.read_sql_query(qry, conn)

    df = pd.DataFrame(sql_query)
    if (format=='json'):
        return df.to_json(index=False, orient='split')
    else:
        return df.to_csv(index=False, header=True)

def truncate_table(sql_table_name):
    '''truncates a table, obviously
    '''
    # create cursor, execute the stmnt
    cursor = connect_db()
    qry = f'''TRUNCATE TABLE {sql_table_name} '''
    cursor.execute(qry)
    row = cursor.fetchone()
    result = str(row[0])
    cursor.close()

    print(f'  truncated table {sql_table_name}:' + str(result))

################################################################ APP ROUTES START HERE

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route("/readme", methods=['GET'])
def readme():
    with open('README.md','r', encoding='utf-8') as f:
        md_template_string = markdown.markdown(
        f.read(), extensions=["fenced_code"]
        )

    return md_template_string

@app.route("/env")
def dump_env():
    try:
        return json.dumps(dict(os.environ),indent=2)
    finally:
        gc.collect()

@app.route("/test_conn")
def test_conn():
    # Obtain connection string information from the portal, copy full string to input
    # getpass hides the value from output, secret manager better option
    # https://stackoverflow.com/questions/54571009/
    # how-to-hide-secret-keys-in-google-colaboratory-from-users-having-the-sharing-lin

    results = ""

    # Construct connection string
    with connect_db() as cursor:
        cursor.execute("SELECT @@Version")
        row = cursor.fetchall()
        results = row

    # Drop previous table of same name if one exists
    cursor.execute("DROP TABLE IF EXISTS inventory;")
    results.append(f"Finished dropping table (if existed).\n")

    # Create table
    cursor.execute("""CREATE TABLE inventory (
                        id INT NOT NULL IDENTITY PRIMARY KEY, 
                        name VARCHAR(50), 
                        quantity INTEGER);""")
    results.append ("Finished creating table.\n")

    # Insert some data into table
    cursor.execute("INSERT INTO inventory (name, quantity) VALUES (?,?);", ("banana", 150))
    results.append("Inserted {} row(s) of data.\n".format(cursor.rowcount))
    cursor.commit()
    cursor.close()
    return (str(results))

@app.route("/load_ticker_info", methods=['GET'])
def load_ticker_info():
    # Get data from query strings
    args = request.args.to_dict()
    tickers = args.get("ticker").split("|")
    print("args:" + str(args))
    for t in tickers:
        # ticker info
        try:
            ticker = yf.Ticker(t)
            df = pd.DataFrame([ticker.info],index=[t])
        except BaseException as err:
            print(f"Unexpected {err}, {type(err)} on {t} in load_ticker_info")

        try:
            # bulk loading with parameterized query only accepts len 510 ascii, UTF double byte
            df["longBusinessSummary"] = df["longBusinessSummary"].str.slice(0, 250)
        except BaseException as err:
            print(f"Unexpected {err}, {type(err)} on {t} in load_ticker_info")
            continue
            
        df.index.names = ['ticker']
        df = df.copy()
        df = df.convert_dtypes()
        # this dump to csv cleans up some formatting problems
        fname = f'{time.time_ns()}_tmp.csv'
        df.to_csv(fname)
        df = pd.read_csv(fname)
        load_from_df('ticker_info', df.copy(deep=True))
        os.remove(fname)
        del df

    gc.collect()
    return '\nFinished ' + str(args) + ' at ' + str(datetime.datetime.now())

@app.route("/load_price_history", methods=['GET'])
def load_price_history():
    # Get data from query strings
    args = request.args.to_dict()
    tickers = args.get("ticker").replace('load_price_history?ticker=','')
    tickers = tickers.split("|")
    print("args:" + str(args))
    print("tickers:" + str(tickers))

    where_clause =  str(tickers).replace("[","").replace("]","")
    where_clause = f"WHERE price_history_tmp.ticker in ({where_clause})" 
    delete_table('price_history_tmp', where_clause)

    # load the tmp table, then compare to main table and insert the new rows
    # some options here https://stackoverflow.com/questions/63107594/
    # how-to-deal-with-multi-level-column-names-downloaded-with-yfinance/63107801#63107801
    for t in tickers:
        # ticker info
        try:
            print(f'starting yahoo api call for ticker {t}\n')
            df = yf.download([t], period="1mo", interval="5m", auto_adjust=True, group_by="column")
            if df.shape[0] ==0:  
                print(f"no data in df from yahoo")
                continue
            print(df.head(1))
        except BaseException as err:
            tb = sys.exc_info()[2]
            print(f"Unexpected {err}, {type(err)}, {err.args} on {t} in load_price_history")
            print('  Exception on ticker {t}:', str(err.with_traceback(tb)))
            continue

        df.reset_index(inplace=True)
        print("index reset:", str(df.head(1)))
        df.loc[:,'Datetime'] = df['Datetime'].astype(str)
        print('datetime updated:', str(df.head(1)))
        df.loc[:,'ticker'] = t
        print('ticker added:\n', str(df.head(1)))
        df2 = df[df['Volume'] > 0].copy(deep=True)
        load_from_df('price_history_tmp', df2) 
        del df
    merge_price_history(where_clause)
    delete_table('price_history_tmp', where_clause)

    gc.collect()
    return '\nFinished ' + str(args) + ' at ' + str(datetime.datetime.now())

@app.route("/dump_table", methods=['GET'])
def dump_table():
    # Get data from query strings
    args = request.args.to_dict()
    print("GET /dump_table?args:" + str(args))
    table, where, format = args.get("table"), args.get("where"), args.get("format")
    if table==None: table='INFORMATION_SCHEMA.COLUMNS'
    if where==None: where='WHERE 1=1'
    if format==None: format='csv'
    table_data = dump_table_to_stream(table=table, where=where, format=format)
    if (format=='csv'):
        return Response(str(table_data), mimetype='text/csv')
    elif (format=='json'):
        return Response(str(table_data), mimetype='application/json')
    else:
        return "ERROR: format parameter mustbe either csv or json"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))