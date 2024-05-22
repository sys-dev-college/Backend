from typing import ClassVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=50,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.LOGLEVEL == "DEBUG",
)

AsyncSessionMaker = async_sessionmaker(
    async_engine,
    autoflush=True,
    expire_on_commit=False,
)


class SessionManager:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session or AsyncSessionMaker()
        self.autoclose = session is None

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()

        if self.autoclose:
            await self.session.close()


class Base(DeclarativeBase):
    __mapper_args__: ClassVar = {"eager_defaults": True}
