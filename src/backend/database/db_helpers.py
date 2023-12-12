import getpass
import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

class Database:
    def __init__(self, db:str = "dsp", host:str = "2001:7c0:2320:2:f816:3eff:fedc:56d9", user:str = "postgres", password:str = "l0r10t", port:str = "5433"):
        ''' Initialize the database
        Input:  - db: str, name of the database
                - host: str, host of the database
                - user: str, user of the database
                - password: str, password of the database
                - port: str, port of the database
        Output: None
        '''
        self.db = db
        self.host = host
        self.user = user
        # Ask for password in terminal if not provided
        if password is None:
            self.password = getpass.getpass(prompt="Database user password: ", stream=None)
        else:
            self.password = password
        self.port = port


    def connect(self):
        ''' Connect to PostgreSQL database via psycopg2 and sqlalchemy
        Input:  self database specific variables
        Output: - conn: connection to the database
                - cur: cursor of the connection
                - engine: engine of the connection (for function pandas_to_sql)
        '''
        # Connect to PostgreSQL database via psycopg2
        self.conn = psycopg2.connect(database=self.db,
                                     host=self.host,
                                     user=self.user,
                                     password=self.password,
                                     port=self.port)
        self.cur = self.conn.cursor()

        # Connect via sqlalchemy
        self.engine = create_engine(f"postgresql+psycopg2://{self.user}:{self.password}@[{self.host}]:{self.port}/{self.db}")

        print('\033[1m\033[92mSuccessfully connected to database.\033[0m')
        return self.conn, self.cur, self.engine


    def disconnect(self) -> None:
        ''' Disconnect from PostgreSQL database via psycopg2
        Input:  - self.conn: connection to the database
                - self.cur: cursor of the connection
                - self.engine: engine of the connection
        Output: None
        '''
        self.cur.close()
        self.conn.close()
        self.engine.dispose()
        print('\033[1m\033[92mSuccessfully disconnected from database.\033[0m')


    def execute_sql(self, sql:str, commit:bool = True):
        ''' Execute an SQL query
        Input:  - self.conn: connection to the database
                - self.cur: cursor of the connection
                - sql: SQL query to execute
                - commit: bool, whether to commit the changes or not
        Output: None
        '''
        # Execute the SQL query
        self.cur.execute(sql)
        if commit:
            self.conn.commit()

        print('\033[1m\033[92mSuccessfully executed SQL query.\033[0m')


    def insert_data(self, data:pd.DataFrame, table:str, if_exists:str = 'append', updated_at:bool = False):
        ''' Insert data into the database
        Input:  - self.engine: connection to the database (via sqlalchemy)
                - data: data to insert
                - table: name of the table to insert the data into
                - if_exists: str, whether to append the data to the table or replace the table
                - updated_at: bool, whether to add current date and time to the data
                ! This function automatically commits the changes !
        Output: None
        '''
        # Add current date and time to the data
        if updated_at:
            data["updated_at"] = pd.to_datetime('today')
        
        # Insert the data
        data.to_sql(table, self.engine, if_exists=if_exists, index=False)

        print('\033[1m\033[92mSuccessfully inserted data into table {}.\033[0m'.format(table))


    def fetch_data(self, total_object:str = None, sql:str = None) -> pd.DataFrame:
        ''' Fetch data from the database
        Input:  - self.engine: connection to the database (via sqlalchemy)
                - total_object: name of the table to fetch all data from
                - sql: SQL query to fetch the data
        Output: list of tuples
        '''
        if total_object is not None:
            sql = f"SELECT * FROM {total_object}"
        
        # Fetch the data
        return pd.read_sql(sql, self.engine)
    

    def delete_data(self, total_object:str, sql:str = None, commit:bool = True):
        ''' Delete data from a database object
        Input:  - self.conn: connection to the database
                - self.cur: cursor of the connection
                - total_object: name of the object to delete all data from
                - sql: SQL query to delete the data
                - commit: bool, whether to commit the changes or not
        Output: None
        '''
        # Delete all data data
        if sql is None:
            sql = f"DELETE FROM {total_object}"

        self.execute_sql(sql, commit=commit)

        print('\033[1m\033[92mSuccessfully deleted data from table {}.\033[0m'.format(total_object))


    def create_db_object(self, object:str = None, sql:str = None, commit:bool = True, drop_if_exists:bool = False):
        ''' Create an object in the database (most convenient with stored sql script under src/backend/database/objects)
        Input:  - self.conn: connection to the database
                - self.cur: cursor of the connection
                - object: name of the table
                - sql: SQL query to create the table
                - commit: bool, whether to commit the changes or not
        Output: None
        '''
        # Drop the table if it exists
        if drop_if_exists:
            self.execute_sql(sql=f"DROP TABLE IF EXISTS {object}", commit=commit)
        
        # Get the stored sql script to create the table
        if sql is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, f"objects/{object}.sql")
            with open(file_path, 'r') as file:
                sql = file.read()
        else:
            print('\033[1m\033[91mWARNING: Please save the object creation script as a sql file under src/backend/database/objects.\033[0m')

        # Execute the SQL query
        self.execute_sql(sql, commit=commit)

        print('\033[1m\033[92mSuccessfully created object{}.\033[0m'.format(" "+object))


    def drop_db_object(self, object:str, sql:str = None, commit:bool = True):
        ''' Drop an object in the database (most convenient with stored sql script under src/backend/database/objects)
        Input:  - self.conn: connection to the database
                - self.cur: cursor of the connection
                - object: name of the table
                - sql: SQL query to drop the table
                - commit: bool, whether to commit the changes or not
        Output: None
        '''
        # SQL query to drop the table
        if sql is None:
            sql = f"DROP TABLE {object}"

        # Execute the SQL query
        self.execute_sql(sql, commit=commit)

        print('\033[1m\033[92mSuccessfully dropped object {}.\033[0m'.format(object))

"""
db = Database()
db.connect()
# TASK

db.disconnect()
"""