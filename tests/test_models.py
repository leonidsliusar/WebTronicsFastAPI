import pytest
from models import UserModel


@pytest.mark.parametrize(
    'first_name, last_name, password, email, expected_message',
    [
        ('test', 'test', 'test', 'test', 'The password isn\'t strong enough'),
        ('test', 'test', 'test', 'test@example.com', 'The password isn\'t strong enough'),
        ('test', 'test', 'test1234', 'test', 'value is not a valid email'),
    ]
)
def test_validate_user_failed(first_name, last_name, password, email, expected_message):
    with pytest.raises(ValueError) as e:
        UserModel(first_name=first_name, last_name=last_name, password=password, email=email)
    assert expected_message in str(e.value)


@pytest.mark.parametrize(
    'first_name, last_name, password, email',
    [
        ('firstname', 'surname', 'Test1234', 'test@example.com')
    ]
)
def test_validate_user(first_name, last_name, password, email):
    user = UserModel(first_name=first_name, last_name=last_name, password=password, email=email)
    assert user
