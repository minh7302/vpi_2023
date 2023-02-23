
from typing import List
import pandas as pd
from pydantic import BaseModel
from pyparsing import Optional
import uvicorn
from db_connect import engine, Session
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
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

Base = declarative_base()
import io
from fastapi import FastAPI, Response
metadata = MetaData(bind=engine)

app = FastAPI()
class Item(BaseModel):
    columns: dict

# class Item(BaseModel):
#     __tablename__ = "user"
#     user_id : str
#     user_name : str
#     password : str
#     role : str
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get('/')
def main(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.put("/api/update/{table_name}/{item_id}")
def update_item(table_name: str, item_id: str, item: Item):
    # create session
    db = Session()

    # get table metadata and build update query
    table = Table(table_name, metadata, autoload=True)
    stmt = text(f"UPDATE {table_name} SET ")
    update_columns = []
    for column_name, column_value in item.columns.items():
        update_columns.append(f"{column_name} = '{column_value}'")
    stmt = stmt + ", ".join(update_columns) + f" WHERE id = '{item_id}'"

    # execute update query and commit changes
    db.execute(stmt)
    db.commit()

    # close session
    db.close()

    # return updated item
    return {"id": item_id, **item.columns}


@app.get("/api/tables/{table_name}")
async def get_table_data(table_name: str):
    session = Session()
    result = session.execute(f"SELECT * FROM public.{table_name}").fetchall()
    session.close()
    
    return [dict(row) for row in result]

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

# # api viết để có thể update mọi thứ 
# @app.put("/api/update/{table_name}")
# async def update_data(table_name: str, data: dict):
#     metadata = MetaData()
#     table = Table(table_name, metadata, autoload=True, autoload_with=engine)
#     session = Session()
#     query = table.update().values(**data)
#     session.execute(query)
#     session.commit()
#     session.close()
#     return {"message": "Data updated successfully"}

# @app.put("/api/update/{table_name}/{field_name}/{field_value}")
# async def update_data(table_name: str, field_name: str, field_value: str, data: dict):
#     with app.app_context():
#         metadata = MetaData()
#         table = Table(table_name, metadata, autoload=True, autoload_with=engine)
#         session = Session()
#         query = table.update().where(getattr(table.c, field_name) == field_value).values(**data)
#         session.execute(query)
#         session.commit()
#         session.close()
#         return {"message": "Data updated successfully"}

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


@app.get("/api/export/{table_name}/{fields}")
async def export_data(table_name: str, fields: str):
    with engine.connect() as connection:
        query = f"SELECT {fields} FROM {table_name}"
        result = connection.execute(query)
        data = [dict(row) for row in result.fetchall()]
        return {"data": data}
    
    
    
@app.post("/api/import/{table_name}")
async def import_data(table_name: str, file: UploadFile):
    df = pd.read_csv(file.file)
    df.to_sql(table_name, engine, if_exists="replace")
    return {"message": "Import thành công"}


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

    return {"data": data}

@app.get("/api/{table_name}")
async def get_items(request: Request, table_name: str, page: int = 1, rowsPerPage: int = 50) -> List[dict]:
    # Load thông tin bảng
    table = Table(table_name, metadata, autoload=True)
    # Thực hiện truy vấn dữ liệu với offset và limit được tính dựa trên start và end
    start = (page - 1) * rowsPerPage
    end = page * rowsPerPage
    stmt = select(table).offset(start).limit(end - start)
    rows = engine.execute(stmt)
    data =  [dict(row) for row in rows]
    return templates.TemplateResponse('index.html', {'request': request, 'data' : data, 'keys' : data[0].keys(), 'table_name': table_name})

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
    return {"data": data}





if __name__ == '__main__':
    uvicorn.run("app:app", reload=True)
