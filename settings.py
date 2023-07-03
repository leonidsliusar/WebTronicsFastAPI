from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_LOGIN: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: str
    DB_TEST_PORT: str
    DB: Optional[str]
    DB_TEST: Optional[str]

    REFRESH_TOKEN_EXPIRES_IN: int
    ACCESS_TOKEN_EXPIRES_IN: int
    ALGORITHM: str
    SECRET_KEY: str

    class Config:
        env_file = '.env'

    def __init__(self):
        super().__init__()
        self.set_db()

    def set_db(self) -> None:
        self.DB = f'postgresql+asyncpg://{self.DB_LOGIN}:{self.DB_PASSWORD}@0.0.0.0:{self.DB_PORT}/{self.DB_NAME}'
        self.DB_TEST = f'postgresql+asyncpg://{self.DB_LOGIN}:{self.DB_PASSWORD}@0.0.0.0:{self.DB_TEST_PORT}/{self.DB_NAME}'


settings = Settings()
