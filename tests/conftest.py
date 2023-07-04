import asyncio
import os
import time
import uuid
import pytest
import redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
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
    os.system('docker rm -f social_test')


@pytest.fixture()
async def get_stub_authenticate(*args, **kwargs):
    return True, 'Ok'


@pytest.fixture()
def get_stub_create_token(*args, **kwargs):
    return '123456'


@pytest.fixture()
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


@pytest.fixture()
def get_stub_user() -> UserModel:
    user_data = {
        "first_name": "firstname",
        "last_name": "lastname",
        "password": "Qwerty1234",
        "email": "foo@example.com"
    }
    return UserModel(**user_data)


@pytest.fixture()
async def get_stub_output_user(*args, **kwargs) -> UserModelOutput:
    user_data = {
        "user_id": uuid.uuid4(),
        "first_name": 'firstname',
        "last_name": 'lastname',
        "email": "foo@example.com"
    }
    return UserModelOutput(**user_data)


@pytest.fixture(scope='function')
def setup_and_teardown_cache() -> None:
    os.system('docker compose -f tests/docker-compose_test_cache.yml up -d')
    r = redis.Redis(host=settings.REDIS_HOST, port=6380, decode_responses=True)
    time.sleep(2)
    yield r
    r.close()
    os.system('docker rm -f social_net_test_cache')


@pytest.fixture(scope='function')
def redis_session():
    r = redis.Redis(host=settings.REDIS_HOST, port=6380, decode_responses=True)
    return r
