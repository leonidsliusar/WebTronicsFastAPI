import uuid
from db.db_services import create_user, get_user
from models import UserModel, UserModelOutput, AuthUser, UserToken


async def test_create_user(setup_and_teardown_db):
    user = UserModel(
        first_name='firstname',
        last_name='lastname',
        password='Qwerty1234',
        email='foo@example.com'
    )
    session = setup_and_teardown_db
    async with session:
        user_to_client = await create_user(user, session)
    assert isinstance(user_to_client, UserModelOutput)
    assert isinstance(user_to_client.user_id, uuid.UUID)
    assert user_to_client.email == user.email
    assert user_to_client.first_name == user.first_name
    assert user_to_client.last_name == user.last_name


async def test_get_user(setup_and_teardown_db):
    user = UserModel(
        first_name='firstname',
        last_name='lastname',
        password='Qwerty1234',
        email='foo@example.com'
    )
    session = setup_and_teardown_db
    async with session:
        await create_user(user, session)
        fetch_user = AuthUser(
            email='foo@example.com',
            password='Qwerty1234'
        )
        user_data = await get_user(fetch_user, session)
    assert isinstance(user_data, dict)
    assert user_data.get('email') == user.email
    assert user_data.get('first_name') == user.first_name
    assert user_data.get('last_name') == user.last_name
    assert isinstance(user_data.get('user_id'), uuid.UUID)
