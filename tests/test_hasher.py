from utils.hasher import hash_pass, check_hash
import pytest
from models import UserModel


@pytest.mark.parametrize(
    'password',
    [
        '123456qweRTYtest',
        'Qwerty1234'
    ]
)
def test_hashing(password):
    user = UserModel(
        first_name='firstname',
        last_name='lastname',
        password=password,
        email='foo@example.com'
        )
    hashed = hash_pass(user.password)
    assert check_hash(password, hashed)
