import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import os
import sys
#add backend folder to sys.path so that .py-files from data directory can be imported as modules
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)
from data.safety_pipeline import create_country_safety_df

#function to connect to database
def connect_to_db(db_name, host, user, password, port):
    conn = psycopg2.connect(database=db_name,
                        host=host,
                        user=user,
                        password=password,
                        port=port)

    cur = conn.cursor()
    engine = create_engine("postgresql+psycopg2://"+user+":"+password+"@["+host+"]:5433/"+db_name)

    return cur, engine, conn

#function to create tables if they do not exist yet
def setup_tables(cur, conn):
    cur.execute("""CREATE TABLE IF NOT EXISTS safety (
            id INT,
            iso2 VARCHAR(2),
            iso3 VARCHAR(3),
            country VARCHAR(32),
            political_stability NUMERIC(7,5),
            rule_of_law NUMERIC(7,5),
            personal_freedom NUMERIC(7,5),
            crime_rate NUMERIC(7,5),
            peace_index NUMERIC(7,5),
            terrorism_index NUMERIC(7,5),
            ecological_threat NUMERIC(7,5)
            );""")
    conn.commit()
    
#function to fill tables if they are empty
def fill_tables(engine):
    source_data = pd.read_sql_table("safety", con=engine)
    if len(source_data) == 0:
        safety_df = create_country_safety_df()
        column_dict = dict(zip(list(safety_df.columns), list(source_data.columns)))
        safety_df.rename(columns=column_dict, inplace=True)
        safety_df.to_sql('safety', engine, if_exists='append', index=False)

#function to print data from specified table
def fetch_data(table):
    sql = "SELECT * FROM "+table+";"
    res = pd.read_sql_query(sql, conn)
    print(res)


cur, engine, conn = connect_to_db(db_name="dsp", host="2001:7c0:2320:2:f816:3eff:fe45:cffc",
                                  user="postgres", password="l0r10t", port="5433")

setup_tables(cur=cur, conn=conn)
fill_tables(engine=engine)
fetch_data(table="safety")

cur.close()
conn.close()
engine.dispose()

