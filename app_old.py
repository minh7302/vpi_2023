import io
from typing import List
import pandas as pd
from pydantic import BaseModel
import uvicorn
from db_connect import engine, Session
from fastapi import FastAPI, HTTPException, Query, Response, UploadFile, File
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData,select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
metadata = MetaData(bind=engine)

app = FastAPI()

@app.get("/api/tables/{table_name}")
async def get_table_data(table_name: str):
    session = Session()
    result = session.execute(f"SELECT * FROM public.{table_name}").fetchall()
    session.close()
    
    return [dict(row) for row in result]
# @app.get("/api/tables/{table_name}")
# async def get_table_data(table_name: str):
#     try:
#         session = Session()
#         table = Table(table_name, metadata, autoload=True)
#         query = table.select()
#         result = session.execute(query).fetchall()
#         session.close()
#         columns = table.columns.keys()  # Lấy danh sách tên cột của bảng
#         return [dict(zip(columns, row)) for row in result]
#     except Exception as e:
#         print(str(e))
#         raise HTTPException(status_code=500, detail=str(e))

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

# api viết để có thể update mọi thứ 
@app.put("/api/update/{table_name}")
async def update_data(table_name: str, data: dict):
    metadata = MetaData()
    table = Table(table_name, metadata, autoload=True, autoload_with=engine)
    session = Session()
    query = table.update().values(**data)
    session.execute(query)
    session.commit()
    session.close()
    return {"message": "Data updated successfully"}

@app.put("/api/update/{table_name}/{field_name}/{field_value}")
async def update_data(table_name: str, field_name: str, field_value: str, data: dict):
    with app.app_context():
        metadata = MetaData()
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        session = Session()
        query = table.update().where(getattr(table.c, field_name) == field_value).values(**data)
        session.execute(query)
        session.commit()
        session.close()
        return {"message": "Data updated successfully"}

@app.delete("/api/delete/cal_curve_value1")
async def delete_cal_curve_value1():
    with app.app_context():
        metadata = MetaData()
        table = Table("cal_curve_value1", metadata, autoload=True, autoload_with=engine)
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
async def export_data(table_name: str, fields: str, response: Response):
    # connect to database
    with Session(engine) as session:
        # select data from the table
        query = text(f"SELECT {fields} FROM public.{table_name}")
        result = session.execute(query)

        # convert data to pandas DataFrame
        data = [dict(row) for row in result.fetchall()]
        df = pd.DataFrame(data)

        # save data to csv file
        output = io.StringIO()
        df.to_csv(output, index=False)

        # return file as response
        contents = output.getvalue()
        response.headers["Content-Disposition"] = f"attachment; filename={table_name}.csv"
        return Response(content=contents, media_type="text/csv")
    
    
@app.post("/api/import/{table_name}")
async def import_data(table_name: str, file: UploadFile):
    df = pd.read_csv(file.file)
    df.to_sql(table_name, engine, if_exists="replace")
    return {"message": "Import thành công"}

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
async def get_items(table_name: str, page: int = 1, rowsPerPage: int = 50) -> List[dict]:
    # Load thông tin bảng
    table = Table(table_name, metadata, autoload=True)
    # Thực hiện truy vấn dữ liệu với offset và limit được tính dựa trên start và end
    start = (page - 1) * rowsPerPage
    end = page * rowsPerPage
    stmt = select(table).offset(start).limit(end - start)
    rows = engine.execute(stmt)
    # Trả về kết quả dưới dạng list các dict

    
    session = Session()
    count_rows = session.execute(f"SELECT count(*) FROM public.{table_name}").fetchall()
    session.close()
    count_page = (count_rows[0])[0]/rowsPerPage

    return [dict(row) for row in rows]


if __name__ == '__main__':
    uvicorn.run("app:app", reload=True)
