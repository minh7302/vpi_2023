from pydantic import BaseSettings


class Settings(BaseSettings):
    POSTGRES_PORT = '5432'
    POSTGRES_PASSWORD = '123456'
    POSTGRES_USER = 'postgres'
    POSTGRES_DB = 'test'
    POSTGRES_HOST = 'localhost'

    JWT_PRIVATE_KEY = 'secrectkey'
    JWT_ALGORITHM = 'HS256'
    REFRESH_TOKEN_EXPIRE_DAYS = 5
    ACCESS_TOKEN_EXPIRE_DAYS = 1

#     JWT_PUBLIC_KEY: str
#     CLIENT_ORIGIN: str

    class Config:
        env_file = './.env'


settings = Settings()
