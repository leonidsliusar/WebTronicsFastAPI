import asyncio
import os
import time
import uuid
from typing import AsyncGenerator, Generator
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
import pytest
import redis
from sqlalchemy import insert, literal_column, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi.testclient import TestClient

from auth_backend.authenticate import create_token, create_refresh_token
from db.db_schema import Post, User
from db.db_services import PostManager
from settings import settings
from db.db_config import get_db
from main import app
from models import UserModel, UserModelOutput


@pytest.fixture(scope='function')
async def setup_and_teardown_db() -> None:
    os.system('docker compose -f tests/docker-compose_test.yml up -d')
    await asyncio.sleep(2)
    os.system('alembic -c alembic_test.ini upgrade head')
    engine = create_async_engine(settings.DB_TEST, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    os.system('docker compose -f tests/docker-compose_test.yml down -v')


@pytest.fixture(scope='class')
def setup_and_teardown_db_integrity() -> None:
    os.system('docker compose -f tests/docker-compose_test.yml up -d')
    time.sleep(2)
    os.system('alembic -c alembic_test.ini upgrade head')
    yield
    os.system('docker compose -f tests/docker-compose_test.yml down -v')


@pytest.fixture()
async def override_dep():
    app.dependency_overrides[get_db] = await get_override_get_db()


async def get_override_get_db():
    engine = create_async_engine(settings.DB_TEST, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> Generator:
        session = async_session()
        try:
            yield session
            await session.commit()
        except IntegrityError:
            raise HTTPException(status_code=409, detail='User already exists')
        finally:
            await session.close()

    return _override_get_db


@pytest.fixture(scope='function')
async def add_stub_user() -> None:
    user_data = {
        "first_name": "firstname",
        "last_name": "lastname",
        "password": "Qwerty1234",
        "email": "foo@example.com"
    }
    engine = create_async_engine(settings.DB_TEST, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=True)
    async with async_session() as session:
        query = insert(User).values(**user_data)
        await session.execute(query)
        await session.commit()


@pytest.fixture(scope='function')
async def stub_user_posts() -> None:
    engine = create_async_engine(settings.DB_TEST, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        query = insert(User).values(first_name='firstname2', last_name='lastname2', password='Qwerty1234',
                                    email='boo@example.com').returning(User.user_id)
        user = await session.execute(query)
        user_id = user.fetchone()[0]
        for i in range(10):
            post = Post()
            post.title = f'test title {i + 1}'
            post.owner_id = user_id
            post.modify_id = user_id
            post.content = f'test content {i + 1}'
            session.add(post)
        await session.flush()
        await session.commit()


@pytest.fixture()
async def get_stub_authenticate(*args, **kwargs):
    return True, 'Ok'


@pytest.fixture()
def get_stub_create_token(*args, **kwargs):
    return '123456'


@pytest.fixture(scope='class')
def get_client() -> TestClient:
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def get_stub_form() -> dict:
    form = {
        'username': 'foo@example.com',
        'password': 'Qwerty1234'
    }
    return form


@pytest.fixture()
def get_stub_form_invalid() -> dict:
    form = {
        'username': 'foo@example.com',
    }
    return form


async def override_get_db():
    yield


@pytest.fixture(scope='class')
def get_stub_user() -> UserModel:
    user_data = {
        "first_name": "firstname",
        "last_name": "lastname",
        "password": "Qwerty1234",
        "email": "foo@example.com"
    }
    return UserModel(**user_data)


@pytest.fixture()
def get_stub_output_user(*args, **kwargs) -> UserModelOutput:
    user_data = {
        "user_id": uuid.uuid4(),
        "first_name": "firstname",
        "last_name": "lastname",
        "email": "foo@example.com"
    }
    return UserModelOutput(**user_data)


@pytest.fixture(scope='class')
def setup_and_teardown_cache():
    os.system('docker compose -f tests/docker-compose_test_cache.yml up -d')
    time.sleep(2)
    yield
    os.system('docker compose -f tests/docker-compose_test_cache.yml down -v')


@pytest.fixture(scope='class')
def redis_session():
    r = redis.Redis(host=settings.REDIS_HOST, port=6380, decode_responses=True)
    yield r
    r.close()


@pytest.fixture(scope='function')
def get_token():
    data = {"sub": "foo@example.com"}
    access_token = create_token(data)
    refresh_token = create_refresh_token(data)[0]
    return access_token, refresh_token
