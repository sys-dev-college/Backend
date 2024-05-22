from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # settings FastAPI
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ItFits Backend"

    SECRET_KEY: str

    JWT_ALGORITHM: str

    SMTP_PASSWORD: str

    INVITE_PROTOCOL: str
    INVITE_DOMAIN: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    MAX_CONTENT_LENGTH: int = 100 * 1024 * 1024  # 100MB

    # settings db
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str

    POSTGRES_TEST_HOST: Optional[str] = None
    POSTGRES_TEST_USER: Optional[str] = None
    POSTGRES_TEST_PASSWORD: Optional[str] = None
    POSTGRES_TEST_DB: Optional[str] = None
    POSTGRES_TEST_PORT: Optional[str] = None

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_TEST_URL(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.POSTGRES_TEST_USER}:{self.POSTGRES_TEST_PASSWORD}@{self.POSTGRES_TEST_HOST}:{self.POSTGRES_TEST_PORT}/{self.POSTGRES_TEST_DB}"

    LOGLEVEL: str = "DEBUG"


    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent



settings = Settings()  # type: ignore
