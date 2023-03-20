
from typing import List
import pandas as pd
from pydantic import BaseModel
from pyparsing import Optional
import uvicorn
from db_connect import engine, Session, get_db, metadata, Base
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, distinct,select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from pydantic import BaseModel
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import csv
from api.auth import PER, PerMission, allow_admin_roles, allow_datamanager_roles, allow_reviewer_roles, login_user
import requests
from api import auth
# Base = declarative_base()
metadata = MetaData(bind=engine)
import io
from fastapi import FastAPI, Response

app = FastAPI()
class Item(BaseModel):
    columns: dict

app.include_router(auth.routes)

# Điều chỉnh cấu hình CORS
origins = [
    "http://localhost",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# class Item(BaseModel):
#     __tablename__ = "user"
#     user_id : str
#     user_name : str
#     password : str
#     role : str
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/')
async def login(request: Request):
    if request.method == 'POST':
        form = await request.form()
        username = form['username']
        password = form['password']
        print(username)
    return templates.TemplateResponse('login.html', {'request': request})

@app.get('/home')
def home(request : Request):
    return templates.TemplateResponse('home.html', {'request':request})

@app.get("/api/tables/{table_name}")
def main(request: Request, table_name: str, rowsPerPage: int = 30):
    form = {
        'username': 'superadmin',
        'password': 'abc123'
    }
    response = requests.post('http://127.0.0.1:8000/auth/token', data=form)
    token = response.json()
    session = Session()
    count_rows = session.execute(f"SELECT count(*) FROM public.{table_name}").fetchall()
    session.close()
    session = Session()
    data = session.execute(f"SELECT * FROM public.{table_name}").fetchall()
    session.close()
    keys = data[0].keys()
    session = Session()
    list_tables = session.execute(f"SELECT distinct well_id FROM public.cal_curve_value").fetchall()
    session.close()
    return templates.TemplateResponse('home.html', {'request': request, 'count_rows':(count_rows[0])[0], 'rowsPerPage':rowsPerPage, 
                                                      'table_name':table_name, 'keys':keys, 'data':data, 'list_tables':list_tables,
                                                      'token' : token})

@app.put("/api/update/{table_name}/{record_id}")
async def update_data(table_name: str, record_id: int, data: dict):
    # Kiểm tra bảng có tồn tại trong CSDL hay không
    if not engine.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Lấy thông tin bảng và kiểm tra cột ID có tồn tại trong bảng hay không
    table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    if 'record_id' not in table.columns.keys():
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' does not have 'record_id' column")

    # Tìm bản ghi cần cập nhật theo ID
    with engine.connect() as conn:
        result = conn.execute(table.select().where(table.c.record_id == record_id)).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail=f"Record with ID '{record_id}' not found in table '{table_name}'")

        # Cập nhật dữ liệu của bản ghi
        update_query = table.update().where(table.c.record_id == record_id).values(data)
        conn.execute(update_query)

    return {"message": f"Record with ID '{record_id}' in table '{table_name}' has been updated."}


@app.post("/api/add/{table_name}")
async def add_data(table_name: str, data: dict):
    metadata = MetaData()
    table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    session = Session()
    query = table.insert().values(**data)
    session.execute(query)
    session.commit()
    session.close()
    return {"message": "Data added successfully"}

@app.delete("/api/delete/cal_curve_value")
async def delete_cal_curve_value1():
    with app.app_context():
        metadata = MetaData()
        table = Table("cal_curve_value", metadata, autoload=True, autoload_with=engine)
        session = Session()
        query = table.delete()
        session.execute(query)
        session.commit()
        session.close()
        return {"message": "Data deleted successfully"}


@app.delete("/api/delete/{table_name}/{field_name}/{field_value}")
async def delete_data(table_name: str, field_name: str, field_value: str):
    table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    session = Session()
    query = table.delete().where(getattr(table.c, field_name) == field_value)
    session.execute(query)
    session.commit()
    session.close()
    return {"message": "Data deleted successfully"}



@app.get("/api/export/{table_name}")
async def export_tables(table_name: str, response: Response):
    session = Session()
    query = text(f"SELECT * FROM {table_name}")
    result = session.execute(query)
    session.close()
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    with io.StringIO() as stream:
        df.to_csv(stream, index=False)
        contents = stream.getvalue()
    
    response.headers["Content-Disposition"] = f"attachment; filename={table_name}.csv"
    return Response(content=contents, media_type="text/csv")


from fastapi.responses import StreamingResponse

@app.get("/api/export/{table_name}/{columns}")
async def export_column_data(table_name: str, columns: str):
    # Load bảng từ CSDL
    try:
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    except:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
    # kiểm tra xem cột có tồn tại trong bảng hay không
    column_list = [c.strip() for c in columns.split(",")]
    invalid_columns = set(column_list) - set(table.columns.keys())
    if invalid_columns:
        raise HTTPException(status_code=404, detail=f"Columns {', '.join(invalid_columns)} do not exist in table '{table.name}'.")
    
    # lấy dữ liệu của các cột từ CSDL
    with engine.connect() as conn:
        query = f"SELECT {', '.join(column_list)} FROM {table_name}"
        result = conn.execute(query).fetchall()
    
    # tạo dataframe từ dữ liệu cột
    df = pd.DataFrame(result, columns=column_list)
    
    # tạo file CSV từ dataframe
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    # trả về file CSV cho người dùng
    return StreamingResponse(buffer, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={table_name}.csv"})

    
    
    
@app.post("/api/import/{table_name}")
async def import_data(table_name: str, file: UploadFile = File(...)):
    # Kiểm tra bảng có tồn tại trong CSDL hay không
    if not engine.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
    # Đọc tập tin CSV và chuyển đổi thành dataframe
    df = pd.read_csv(file.file)
    
    # Thêm dữ liệu từ dataframe vào bảng đã có sẵn
    df.to_sql(table_name, engine, if_exists='append', index=False)
    
    # Trả về kết quả thành công
    return {"message": "Data imported successfully."}


#API chọn ra các bảng A10,A15 trong cal_curve_value
@app.get("/api/get_data/{table_name}/{field_name}/{field_value}")
def get_data(table_name: str, field_name: str, field_value: str):
    # Lấy dữ liệu từ bảng
    table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    query = select([table]).where(getattr(table.c, field_name) == field_value)
    results = engine.execute(query).fetchall()
    
    # Chuyển kết quả thành dạng dictionary
    data = []
    for row in results:
        row_dict = {}
        for col in row.keys():
            row_dict[col] = row[col]
        data.append(row_dict)

    return data




@app.get("/api/{table_name}", dependencies=[Depends(login_user)])
async def get_items(table_name: str, db : Session = Depends(get_db), page: int = 1, rowsPerPage: int = 30) -> List[dict]:
    # Load thông tin bảng
    table = Table(table_name, metadata, autoload=True)
    # Thực hiện truy vấn dữ liệu với offset và limit được tính dựa trên start và end
    start = (page - 1) * rowsPerPage
    end = page * rowsPerPage
    stmt = select(table).order_by(table.c.record_id).offset(start).limit(end - start)
    rows = db.execute(stmt)
    # Trả về kết quả dưới dạng list các dict
    return [dict(row) for row in rows]


# def main(request: Request):
#     return templates.TemplateResponse('index.html', {'request': request})


# API lấy dữ liệu từ bảng theo cột và các giá trị trong cột phải là duy nhất
@app.get("/api/{table_name}/{column_name}/unique")
async def get_unique_column_values(table_name: str, column_name: str) -> List[str]:
    # lấy metadata của bảng từ engine
    metadata.reflect(bind=engine)
    
    # lấy đối tượng bảng từ metadata
    table = metadata.tables[table_name]
    
    # tạo câu truy vấn SQL để lấy giá trị không trùng lặp của cột
    stmt = select(distinct(table.columns[column_name]))
    
    # thực hiện câu truy vấn và trả về kết quả dưới dạng danh sách các giá trị
    rows = engine.execute(stmt)
    return [row[0] for row in rows]

@app.get("/import_table")
def home(request : Request):
    return templates.TemplateResponse('import_file.html', {'request':request})

if __name__ == '__main__':
    uvicorn.run("app:app", reload=True)


