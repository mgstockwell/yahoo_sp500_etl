import os
import yfinance
import pyodbc
from flask import Flask
from getpass import getpass

app = Flask(__name__)

conn_string = os.environ.get("azure_conn_string")

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route("/test_conn")
def test_conn():
    # Obtain connection string information from the portal, copy full string to input
    # getpass hides the value from output, secret manager better option
    # https://stackoverflow.com/questions/54571009/
    # how-to-hide-secret-keys-in-google-colaboratory-from-users-having-the-sharing-lin

    results = ""

    # Construct connection string
    with pyodbc.connect(conn_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT @@Version")
            row = cursor.fetchall()
            print(row)

    # Drop previous table of same name if one exists
    cursor.execute("DROP TABLE IF EXISTS inventory;")
    results = "Finished dropping table (if existed).\n"

    # Create table
    cursor.execute("""CREATE TABLE inventory (
                        id INT NOT NULL IDENTITY PRIMARY KEY, 
                        name VARCHAR(50), 
                        quantity INTEGER);""")
    results = results + ("Finished creating table.\n")

    # Insert some data into table
    cursor.execute("INSERT INTO inventory (name, quantity) VALUES (?,?);", ("banana", 150))
    results = results + "Inserted",cursor.rowcount,"row(s) of data.\n"
    cursor.execute("INSERT INTO inventory (name, quantity) VALUES (?,?);", ("orange", 154))
    results = results + ("Inserted",cursor.rowcount,"row(s) of data.\n")
    cursor.execute("INSERT INTO inventory (name, quantity) VALUES (?,?);", ("apple", 100))
    results = results + ("Inserted",cursor.rowcount,"row(s) of data.\n")

    # Cleanup
    conn.commit()
    cursor.close()

    return results


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))