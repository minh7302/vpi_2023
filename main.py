import pandas as pd
from db_connect import engine, Session
from flask import Flask, jsonify, make_response, request
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
metadata = MetaData()

app = Flask(__name__)

@app.route("/api/tables/<table_name>", methods=["GET"])
def get_table_data(table_name):
    session = Session()
    result = session.execute(f"SELECT * FROM {table_name}").fetchall()
    session.close()
    
    return jsonify([dict(row) for row in result])

@app.route("/api/add/<table_name>", methods=["POST"])
def add_data(table_name):
    with app.app_context():
        metadata = MetaData()
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        session = Session()
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        data = request.get_json()
        query = table.insert().values(**data)
        session.execute(query)
        session.commit()
        session.close()
        return jsonify({"message": "Data added successfully"}), 201

# api viết để có thể update mọi thứ 
@app.route("/api/update/<table_name>", methods=["PUT"])
def update_data(table_name):
    with app.app_context():
        metadata = MetaData()
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        session = Session()
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        data = request.get_json()
        query = table.update().values(**data)
        session.execute(query)
        session.commit()
        session.close()
        return jsonify({"message": "Data updated successfully"}), 200

# api viết để có thể update theo trường 
@app.route("/api/update/<table_name>/<field_name>/<field_value>", methods=["PUT"])
def update_data1(table_name, field_name, field_value):
    with app.app_context():
        metadata = MetaData()
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        session = Session()
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        data = request.get_json()
        query = table.update().where(getattr(table.c, field_name) == field_value).values(**data)
        session.execute(query)
        session.commit()
        session.close()
        return jsonify({"message": "Data updated successfully"}), 200


# api xóa full bảng 
@app.route("/api/delete/cal_curve_value1", methods=["DELETE"])
def delete_cal_curve_value1():
    with app.app_context():
        metadata = MetaData()
        table = Table("cal_curve_value1", metadata, autoload=True, autoload_with=engine)
        session = Session()
        query = table.delete()
        session.execute(query)
        session.commit()
        session.close()
        return jsonify({"message": "Data deleted successfully"}), 200

# api xóa theo trường và giá trị 
@app.route("/api/delete/<table_name>/<field_name>/<field_value>", methods=["DELETE"])
def delete_data(table_name, field_name, field_value):
    with app.app_context():
        metadata = MetaData()
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        session = Session()
        query = table.delete().where(getattr(table.c, field_name) == field_value)
        session.execute(query)
        session.commit()
        session.close()
        return jsonify({"message": "Data deleted successfully"}), 200
    

@app.route("/api/export/<table_name>", methods=["GET"])
def export_tables(table_name):
    session = Session()
    query = text(f"SELECT * FROM {table_name}")
    result = session.execute(query)
    session.close()

    df = pd.DataFrame(result.fetchall(), columns=result.keys())

    response = make_response(df.to_csv())
    response.headers["Content-Disposition"] = f"attachment; filename={table_name}.csv"
    response.headers["Content-Type"] = "text/csv"

    return response



@app.route("/api/import/<tables>", methods=["POST"])
def import_cal_curve_value1(tables):
    session = Session()
    file = request.files["file"]
    df = pd.read_csv(file)
    df.to_sql(f"{tables}", engine, if_exists="replace")
    session.commit()
    session.close()
    
    return "Import success"

if __name__ == '__main__':
    app.run(debug=True)



