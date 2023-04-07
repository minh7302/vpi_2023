
from typing import List
import pandas as pd
from pydantic import BaseModel
from pyparsing import Optional
import uvicorn
from db_connect import engine, Session, get_db, metadata, Base
from fastapi import FastAPI, Form, HTTPException, Query, UploadFile, File, Depends
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
import csv, json
import requests
from tempfile import NamedTemporaryFile
import pandas as pd
# Base = declarative_base()
import io
from fastapi import FastAPI, Response
import numpy as np
from api.auth import PER, PerMission, allow_admin_roles, allow_datamanager_roles, allow_reviewer_roles, login_user
from api import auth
from starlette.middleware.sessions import SessionMiddleware

metadata = MetaData(bind=engine)

app = FastAPI()
class Item(BaseModel):
    columns: dict

app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
app.mount("/static", StaticFiles(directory="static"), name="static")
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

@app.get("/")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@app.post("/home")
async def login(request: Request, token: str = Form(...)):
    session = Session()
    list_tables = session.execute(f"SELECT distinct well_id FROM public.cal_curve_value").fetchall()
    session.close()
    request.session['token'] = token
    return templates.TemplateResponse('home.html', {"request": request, 'list_tables':list_tables})

@app.get('/logout')
async def login_form(request: Request):
    request.session.pop('token')
    return templates.TemplateResponse("login.html", {"request": request})

#render về home.html
@app.get("/tables/{well_id}")
def main(request: Request, well_id: str, rowsPerPage: int = 30):
    session = Session()
    count_curve = session.execute(f"select count(distinct curve_id) from cal_curve_value where well_id like '{well_id}'").fetchall()
    session.close()
    session = Session()
    data = session.execute(f"select * from cal_curve_value").fetchall()
    session.close()
    keys = data[0].keys()
    session = Session()
    list_tables = session.execute(f"SELECT distinct well_id FROM public.cal_curve_value").fetchall()
    session.close()
    token = request.session['token']
    return templates.TemplateResponse('home.html', {'request': request, 'rowsPerPage':rowsPerPage, 'token' : token,
                                                      'well_id':well_id, 'keys':keys, 'data':data, 'list_tables':list_tables})

#lấy dữ liệu trong bảng cal_curve_value có cur_id = value (A10,A15)
@app.get("/api/cal_curve_value/{value}")
def get_data_cal_curve_value(value: str, page: int = 1, rowsPerPage: int = 30):
    # Lấy dữ liệu từ bảng
    session = Session()
    count_curve = session.execute(f"select count(distinct curve_id) from cal_curve_value where well_id like '{value}'").fetchall()
    session.close()
    session = Session()
    count_rows = session.execute(f"select count(*) from cal_curve_value where well_id like '{value}'").fetchall()
    session.close()
    rowsPerPage = rowsPerPage * (count_curve[0])[0]
    table = Table('cal_curve_value', metadata, autoload=True, autoload_with=engine)
    start = (page - 1) * rowsPerPage
    end = page * rowsPerPage
    query = select([table]).where(getattr(table.c, 'well_id') == value).order_by(table.c.md).offset(start).limit(end - start)
    results = engine.execute(query).fetchall()
    data = []
    for row in results:
        row_dict = {}
        for col in row.keys():
            row_dict[col] = row[col]
        data.append(row_dict)
    new_data = {
        'records': data,
        'count_rows': int((count_rows[0])[0] / (count_curve[0])[0])
    }
    return new_data

#Lấy dữ liệu từ API trên, xoay dữ liệu 
@app.get('/api/pivot_table/{well_id}', dependencies=[Depends(login_user)])
def pivot_table_1(well_id: str, min_md: float = None, max_md: float = None, page: int = 1, page_size: int = 30):
    # Lấy dữ liệu từ API
    df = requests.get(f"http://127.0.0.1:8000/api/cal_curve_value/{well_id}?page={page}&rowsPerPage={page_size}")
    df = df.json()
    temp = df['records']
    count_rows = df['count_rows']
    if min_md < (temp[0])['md'] : min_md = (temp[0])['md']
    count_rows = int(count_rows - min_md + (temp[0])['md'])
    if max_md != None: count_rows = max_md - min_md
    # Tạo dataframe và xóa các giá trị trùng lặp
    df = pd.DataFrame(temp)
    df = df.drop_duplicates(subset=['md', 'curve_id'])
    
    # Chọn các giá trị trong khoảng từ min_md đến max_md (nếu có)
    if min_md is not None:
        df = df[df['md'] >= min_md]
        if max_md is not None:
            df = df[df['md'] <= max_md]
    
    # Chọn các cột để xoay bảng
    columns = ['md', 'curve_id', 'cal_value']

    # Xoay bảng
    df = df[columns].pivot(index='md', columns='curve_id', values='cal_value')

    # Thay thế giá trị NaN bằng 0
    df = df.replace(np.nan, 0)
    # Chuyển đổi dataframe thành danh sách các đối tượng JSON
    json_list = []
    for index, row in df.iterrows():
        json_obj = {"md": index}
        for col in df.columns:
            json_obj[col] = row[col]
        json_list.append(json_obj)
    new_data = {
        'records': json_list,
        'count_rows': count_rows
    }
    return new_data


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
    
    # tạo file CSV từ dữ liệu cột
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(column_list)
    for row in result:
        writer.writerow(row)
    buffer.seek(0)
    
    # trả về file CSV cho người dùng
    content = buffer.getvalue().encode("utf-8")
    headers = {
        "Content-Disposition": f"attachment; filename={table_name}.csv",
        "Content-Type": "text/csv",
        "Content-Length": str(len(content)),
    }
    return Response(content=content, headers=headers)


@app.post("/api/import/{table_name}")
async def import_data(table_name: str, file: UploadFile = File(...)):
    # Kiểm tra bảng có tồn tại trong CSDL hay không
    if not engine.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table c'{table_name}' not found")
        
    # Lưu file vào bộ nhớ tạm
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp.flush()
        tmp.seek(0)
        df_new = pd.read_csv(tmp)
        
    # Lấy dữ liệu từ bảng đã có sẵn
    df_old = pd.read_sql_table(table_name, engine)
    
    # Ghép dữ liệu mới và cũ lại với nhau để kiểm tra trùng lặp
    df_merged = pd.concat([df_old, df_new], axis=0)
    
    # Kiểm tra trùng lặp
    duplicate_rows = df_merged[df_merged.duplicated(keep=False)]
    if not duplicate_rows.empty:
        raise HTTPException(status_code=400, detail="Dữ liệu import vào chứa các hàng trùng lặp")
    
    # Thêm dữ liệu từ dataframe vào bảng đã có sẵn
    df_new.to_sql(table_name, engine, if_exists='append', index=False)
    
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

@app.get("/api/{table_name}")
async def get_items(table_name: str, db : Session = Depends(get_db), page: int = 1, rowsPerPage: int = 30) -> List[dict]:
    # Load thông tin bảng
    table = Table(table_name, metadata, autoload=True)
    # Thực hiện truy vấn dữ liệu với offset và limit được tính dựa trên start và end
    first_col = str(table.columns.keys()[0])

    start = (page - 1) * rowsPerPage
    end = page * rowsPerPage
    stmt = select(table).order_by(table.c[first_col]).offset(start).limit(end - start)
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




# APi chọn giá trị duy nhất trong từng bảng theo curve_id 
@app.get("/api/unique_curve_ids/{well_id}")
async def get_unique_curve_ids(well_id: str):
    # Lấy danh sách các giá trị duy nhất của trường curve_id dựa trên well_id
    query = f"SELECT DISTINCT curve_id FROM cal_curve_value WHERE well_id = '{well_id}'"
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    # Chuyển kết quả từ tuple sang list
    result = [row[0] for row in rows]

    return result

# Viết API lấy curve_id phụ thuộc vào well_id 
@app.get("/api/get_data/cal_curve_value/well_id/{well_id}/{curve_id}")
def get_cal_curve_data(well_id: str, curve_id: str):
    # Lấy dữ liệu từ bảng cal_curve_value với điều kiện well_id và curve_id
    table = Table("cal_curve_value", metadata, autoload=True, autoload_with=engine)
    query = select([table]).where(and_(table.c.well_id == well_id, table.c.curve_id == curve_id))
    results = engine.execute(query).fetchall()
    # Chuyển kết quả thành dạng dictionary
    data = []
    for row in results:
        row_dict = {}
        for col in row.keys():
            row_dict[col] = row[col]
        data.append(row_dict)
    return data


if __name__ == '__main__':
    uvicorn.run("app:app", reload=True)


