from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres:huy31072002@127.0.0.1/vpi1")
Session = sessionmaker(bind=engine)

