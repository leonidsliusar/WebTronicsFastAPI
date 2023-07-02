import uuid
from db.db_services import create_user
from models import UserModel, UserModelOutput


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
