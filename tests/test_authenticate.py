import pytest
from fastapi import HTTPException
from auth_backend.authenticate import authenticate, create_token, decode_token, get_user_from_token
from db.db_services import create_user
from models import AuthUser, UserModel


@pytest.mark.parametrize('password_create, email_create, password_check, email_check, result', [
                        ('Qwerty1234', 'foo@example.com', 'Qwerty1234', 'foo@example.com', (True, 'Ok')),
                        ('Qwerty1234', 'foo@example.com', 'qwertY1234', 'foo@example.com', (False, 'Invalid password')),
                        ('Qwerty1234', 'foo@example.com', 'Qwerty1234', 'too@example.com', (False, 'Invalid email'))
                            ]
                         )
async def test_authenticate(setup_and_teardown_db, password_create, email_create, password_check, email_check, result):
    user = UserModel(
        first_name='foo',
        last_name='foo',
        password=password_create,
        email=email_create
    )
    session = setup_and_teardown_db
    async with session:
        await create_user(user, session)
        user_data = AuthUser(
            email=email_check,
            password=password_check
        )
        flag = await authenticate(user_data, session)
    assert flag == result


async def test_create_token():
    token = create_token({'sub': 'foo@example.com'})
    payload_from_token = decode_token(token)
    assert payload_from_token.get('sub') == 'foo@example.com'
    assert payload_from_token['exp']


async def test_get_user_from_token(setup_and_teardown_db):
    user = UserModel(
        first_name='foo',
        last_name='foo',
        password='Qwerty1234',
        email='foo@example.com'
    )
    token = create_token({'sub': 'foo@example.com'})
    session = setup_and_teardown_db
    async with session:
        await create_user(user, session)
        user_data = await get_user_from_token(token, session)
    assert user_data.get('first_name') == user.first_name
    assert user_data.get('last_name') == user.last_name
    assert user_data.get('email') == user.email
    for key in ('is_admin', 'user_id'):
        assert key in user_data


@pytest.mark.parametrize('email, token, expected_result', [
                        ('too@example.com', None, ('401', 'Could not validate credentials')),
                        ('foo@example.com', '123456', ('401', 'Could not validate credentials')),
                        ]
                         )
async def test_failed_user_from_token(setup_and_teardown_db, email, token, expected_result):
    user = UserModel(
        first_name='foo',
        last_name='foo',
        password='Qwerty1234',
        email='foo@example.com'
    )
    token = token if token else create_token({'sub': email})
    session = setup_and_teardown_db
    async with session:
        await create_user(user, session)
        with pytest.raises(HTTPException) as e:
            await get_user_from_token(token, session)
    assert e.value.status_code, e.value.detail == expected_result


async def test_failed_user_from_invalid_token(setup_and_teardown_db):
    user = UserModel(
        first_name='foo',
        last_name='foo',
        password='Qwerty1234',
        email='foo@example.com'
    )
    token = create_token({'sub': 'foo@example.com'})
    session = setup_and_teardown_db
    async with session:
        await create_user(user, session)
        with pytest.raises(HTTPException) as e:
            await get_user_from_token(token*2, session)
    assert e.value.status_code, e.value.detail == ('401', 'Could not validate credentials')