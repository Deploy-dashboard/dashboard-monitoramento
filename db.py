import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import urllib
import streamlit as st

load_dotenv()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

@st.cache_resource
def conecta_banco():

    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=10.10.4.13,61433;"
        f"DATABASE=TD_DASHBOARD_CPD;"
        f"UID={user};"
        f"PWD={password};"
    )

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    return engine




