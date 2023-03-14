
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("postgresql://postgres:huy31072002@127.0.0.1/vpi1")
Session = sessionmaker(bind=engine, autocommit= False, autoflush= False)
Base = declarative_base()
metadata = MetaData()
metadata.reflect(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
