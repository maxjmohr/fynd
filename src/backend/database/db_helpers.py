import os
import pandas as pd
import psycopg2
import re
from sqlalchemy import create_engine
import warnings

def connect_to_db(db:str = "dsp", host:str = "2001:7c0:2320:2:f816:3eff:fe45:cffc", user:str = "postgres", password:str = "l0r10t", port:str = "5433"):
    ''' Connect to PostgreSQL database via psycopg2 and sqlalchemy
    Input:  - db: str, name of the database
            - host: str, host of the database
            - user: str, user of the database
            - password: str, password of the database
            - port: str, port of the database
    Output: - conn: connection to the database
            - cur: cursor of the connection
            - engine: engine of the connection (for function pandas_to_sql)
    '''
    # Connect to PostgreSQL database via psycopg2
    conn = psycopg2.connect(database=db,
                host=host,
                user=user,
                password=password,
                port=port)
    cur = conn.cursor()

    # Connect via sqlalchemy
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@[{host}]:{port}/{db}")

    print('\033[1m\033[92mSuccessfully connected to database.\033[0m')
    return conn, cur, engine


def disconnect_from_db(conn, cur, engine) -> None:
    ''' Disconnect from PostgreSQL database via psycopg2
    Input:  - conn: connection to the database
            - cur: cursor of the connection
            - engine: engine of the connection
    Output: None
    '''
    cur.close()
    conn.close()
    engine.dispose()
    print('\033[1m\033[92mSuccessfully disconnected from database.\033[0m')


def execute_sql(conn, cur, sql:str, commit:bool = True):
    ''' Execute an SQL query
    Input:  - conn: connection to the database
            - cur: cursor of the connection
            - sql: SQL query to execute
            - commit: bool, whether to commit the changes or not
    Output: None
    '''
    # Execute the SQL query
    cur.execute(sql)
    if commit:
        conn.commit()

    print('\033[1m\033[92mSuccessfully executed SQL query.\033[0m')


def insert_data(engine, data:pd.DataFrame, table:str, if_exists:str = 'append'):
    ''' Insert data into the database
    Input:  - engine: connection to the database (via sqlalchemy)
            - cur: cursor of the connection
            - data: data to insert
            - table: name of the table to insert the data into
            - if_exists: str, whether to append the data to the table or replace the table
            ! This function automatically commits the changes !
    Output: None
    '''
    # Insert the data
    data.to_sql(table, engine, if_exists='append', index=False)

    print('\033[1m\033[92mSuccessfully inserted data into table {}.\033[0m'.format(table))


def fetch_data(engine, total_object:str, sql:str = None) -> pd.DataFrame:
    ''' Fetch data from the database
    Input:  - engine: connection to the database (via sqlalchemy)
            - cur: cursor of the connection
            - sql: SQL query to fetch the data
    Output: list of tuples
    '''
    if total_object is not None:
        sql = f"SELECT * FROM {total_object}"
    
    # Fetch the data
    return pd.read_sql(sql, engine)


def create_db_object(conn, cur, object:str = None, sql:str = None, commit:bool = True):
    ''' Create an object in the database (most convenient with stored sql script under src/backend/database/objects)
    Input:  - conn: connection to the database
            - cur: cursor of the connection
            - object: name of the table
            - sql: SQL query to create the table
            - commit: bool, whether to commit the changes or not
    Output: None
    '''
    if sql is None:
        # Get the stored sql script to create the table
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, f"objects/{object}.sql")
        with open(file_path, 'r') as file:
            sql = file.read()
    else:
        warnings.warn("WARNING: Please save the object creation script as a sql file under src/backend/database/objects.")

    # Execute the SQL query
    cur.execute(sql)
    if commit:
        conn.commit()

    print('\033[1m\033[92mSuccessfully created object{}.\033[0m'.format(" "+object))