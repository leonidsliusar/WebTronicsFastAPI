from typing import Generator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import settings

engine = create_async_engine(settings.DB, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> Generator:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
