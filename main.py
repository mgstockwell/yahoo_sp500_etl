from ast import arg
import os, sys, json
from posixpath import split
import requests
import datetime
import pandas as pd
from matplotlib.font_manager import json_dump
import yfinance as yf
import pyodbc
from flask import Flask, request
from getpass4 import getpass

app = Flask(__name__)

conn_string = os.environ.get("AZURE_CONN_STRING")

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

def load_from_df(sql_table_name, df: pd.DataFrame):
    '''Loads data to SQL server from dataframe
    '''
    df = df.fillna(0)
    df.index.names = ['ticker']
    df.convert_dtypes()

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
    print('  df columns:', df.columns.to_list())

    # select columns from dataframe that are in the sql table
    common_cols = set(col_list) & set(df.columns.to_list())
    print('COMMON COLS:',common_cols)
    col_count = len(common_cols)
    df = df[common_cols]

    # vals is list of question marks for each column for insert stmnt
    vals = ('?,' *(col_count -1) ) + '?'
    col_list = str(common_cols).replace("'",'"')
    col_list = col_list.replace('{','').replace('}','')
    insert_tbl_stmt = f"INSERT INTO {sql_table_name} ({col_list}) values({vals})"
    print("   insert statement:", insert_tbl_stmt)

    # insert rows
    try:
        cursor.executemany(insert_tbl_stmt, df.values.tolist())
        cursor.commit()
        print(f'   {len(df)} rows inserted into {sql_table_name} table', datetime.datetime.now())
    except BaseException as err:
        print(f"   Unexpected {err}, {type(err)}")
    finally:
        cursor.close()
    
    return 'Completed load_ticker_info ' + str(datetime.datetime.now())

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route("/env")
def dump_env():
    return json.dumps(dict(os.environ),indent=2)

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
    results.append("Finished dropping table (if existed).\n")

    # Create table
    cursor.execute("""CREATE TABLE inventory (
                        id INT NOT NULL IDENTITY PRIMARY KEY, 
                        name VARCHAR(50), 
                        quantity INTEGER);""")
    results.append ("Finished creating table.\n")

    # Insert some data into table
    cursor.execute("INSERT INTO inventory (name, quantity) VALUES (?,?);", ("banana", 150))
    results.append("Inserted {} row(s) of data.\n".format(cursor.rowcount))
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
        df = df.convert_dtypes()
        df.to_csv('tmp.csv')
        df = pd.read_csv('tmp.csv')
        load_from_df('ticker_info', df)
        return 'Finished ' + t + ' at ' + str(datetime.datetime.now())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))