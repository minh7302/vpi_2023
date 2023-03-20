from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import settings

# DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/vpi1"
DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()
metadata.reflect(bind=engine)


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# database = Database(DATABASE_URL)
# session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
