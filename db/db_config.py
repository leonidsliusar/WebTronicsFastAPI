from typing import Generator

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(settings.DB, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> Generator:
    session = async_session()
    try:
        yield session
        await session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='User already exists')
    finally:
        await session.close()
