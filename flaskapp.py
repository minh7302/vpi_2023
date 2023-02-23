from flask import Flask, render_template
import requests
from db_connect import engine, Session
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData,select
from sqlalchemy import text
metadata = MetaData(bind=engine)

app = Flask(__name__)
@app.route('/')
def home():
     return render_template('index.html')
@app.route('/<table_name>')
def index(table_name):
     session = Session()
     count_rows = session.execute(f"SELECT count(*) FROM {table_name}").fetchall()
     session.close()
     count_page = int((count_rows[0])[0]/50)
     print(count_page)
     data = requests.get(f"http://127.0.0.1:8000/api/{table_name}")
     keys = data.json()[0].keys()
     return render_template('index.html', data = data.json(), keys = keys, count_page = count_page, table_name = table_name)