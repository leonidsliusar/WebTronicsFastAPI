import asyncio
import copy
import time

import pytest
from starlette.testclient import TestClient

from db.db_schema import Post
from models import UserModel, PostModel, UpdatePostModel


@pytest.mark.usefixtures('setup_and_teardown_db_integrity', 'setup_and_teardown_cache', 'get_client', 'get_stub_user',
                         'override_dep', 'setup_and_teardown_cache', 'redis_session')
class TestIntegrityAPI:
    access_token: str
    refresh_token: str
    user_data: dict

    @classmethod
    def set_data(cls, key, value):
        setattr(cls, key, value)

    async def test_registration(self, get_client: TestClient, get_stub_user: UserModel):
        response = get_client.post('/reg', json=get_stub_user.dict())
        user = get_stub_user
        user_data = {'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}
        assert set(user_data.items()).issubset(set(response.json().items()))
        assert response.status_code == 200
        user_data.update(response.json())
        user_data.update(user.__dict__)
        user_data.update({'username': user_data.get('email')})
        self.set_data('user_data', user_data)

    async def test_authentication(self, get_client: TestClient):
        data = copy.copy(self.user_data)
        for key in ('user_id', 'first_name', 'last_name', 'email'):
            data.pop(key)
        response = get_client.post('/login/token', data=data)
        refresh_token = response.cookies.get('refresh_token')
        assert refresh_token
        self.set_data('refresh_token', refresh_token)
        access_token = response.json().get('access_token')
        self.set_data('access_token', access_token)
        assert response.status_code == 200
        assert response.json().get('token_type') == 'bearer'

    async def test_refresh_token(self, get_client: TestClient):
        time.sleep(1)
        response = get_client.post('/refresh', cookies={'refresh_token': self.refresh_token})
        new_access_token = response.json().get('access_token')
        assert self.access_token != new_access_token
        self.set_data('access_token', new_access_token)

    async def test_new_post(self, get_client: TestClient, stub_user_posts):
        data = {
            "title": "Some Title 11",
            "content": "Some Content 11",
        }
        post = PostModel(**data)
        response = get_client.post('/post', headers={'Authorization': f'bearer {self.access_token}'}, data=post.json())
        assert response.status_code == 200

    async def test_read_posts(self, get_client: TestClient):
        response = get_client.get('/post', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert len(response.json()) == 11

    @pytest.mark.parametrize('page, limit, length, expected, exp_code', [
        (0, 5, 5, range(1, 6), 200),
        (1, 10, None, None, 404),
        (2, 2, 2, range(6, 8), 200),
        (0, 100, 11, range(1, 12), 200),
        (0, 0, None, None, 422)
    ]
                             )
    async def test_read_posts_filter(self, get_client: TestClient, page, limit, length, expected, exp_code):
        response = get_client.get(f'/post/filter?page={page}&limit={limit}',
                                  headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == exp_code
        if response.status_code == 200:
            assert len(response.json()) == length
            assert [int(post.get('title').split(' ')[2]) for post in response.json()] == list(expected)

    async def test_read_post(self, get_client: TestClient):
        response = get_client.get('/post/1', headers={'Authorization': f'bearer {self.access_token}'})
        assert len(response.json()) == 7
        assert response.status_code == 200
        assert int(response.json().get('title').split(' ')[2]) == 1

    @pytest.mark.parametrize('post_id, expected_result, expected_code', [
        (1, 'You haven\'t permission for modify 1', 403),
        (11, None, 200)
    ]
                             )
    async def test_update_post(self, get_client: TestClient, post_id, expected_result, expected_code):
        data = {'title': 'The Brand New Test Post', 'content': 'something'}
        post = PostModel(**data)
        header = {'Authorization': f'bearer {self.access_token}'}
        response = get_client.put(f'/post/{post_id}', headers=header, data=post.json())
        assert response.status_code == expected_code
        if response.status_code != 200:
            assert response.json().get('detail') == expected_result

    @pytest.mark.parametrize('post_id, expected_result, expected_code', [
        (1, 'You haven\'t permission for modify 1', 403),
        (11, None, 204)
    ]
                             )
    async def test_remove_post(self, get_client: TestClient, post_id, expected_result, expected_code):
        response = get_client.delete(f'/post/{post_id}', headers={'Authorization': f'bearer {self.access_token}'})
        response_check = get_client.get(f'/post/{post_id}', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == expected_code
        if response.status_code != 204:
            assert response.json().get('detail') == expected_result
            assert response_check.json()
        if response.status_code == 204:
            response_check.json().get('detail') == f'Post {post_id} doesn\'t exists'

    @pytest.mark.parametrize('post_id, expected_result', [
        (1, {'1': 1})
    ]
                             )
    async def test_add_like(self, redis_session, monkeypatch, get_client: TestClient, post_id, expected_result):
        monkeypatch.setattr('cache_redis.cache.r', redis_session)
        response = get_client.post(f'/post/{post_id}/like', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert response.json() == expected_result

    @pytest.mark.parametrize('post_id, expected_result', [
        (1, {'1': 0})
    ]
                             )
    async def test_remove_like(self, monkeypatch, redis_session, get_client: TestClient, post_id, expected_result):
        monkeypatch.setattr('cache_redis.cache.r', redis_session)
        response = get_client.delete(f'/post/{post_id}/like', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert response.json() == expected_result

    @pytest.mark.parametrize('post_id, expected_result', [
        (1, {'1': 1})
    ]
                             )
    async def test_add_dis(self, redis_session, monkeypatch, get_client: TestClient, post_id, expected_result):
        monkeypatch.setattr('cache_redis.cache.r', redis_session)
        response = get_client.post(f'/post/{post_id}/dis', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert response.json() == expected_result

    @pytest.mark.parametrize('post_id, expected_result', [
        (1, {'1': 0})
    ]
                             )
    async def test_remove_dis(self, monkeypatch, redis_session, get_client: TestClient, post_id, expected_result):
        monkeypatch.setattr('cache_redis.cache.r', redis_session)
        response = get_client.delete(f'/post/{post_id}/dis', headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert response.json() == expected_result

    async def test_show_like(self, monkeypatch, redis_session, get_client: TestClient, post_id=1):
        expected_result = {
        'total_likes': 0,
        'user_set_likes': [],
        'total_dislikes': 0,
        'user_set_dislikes': [],
            }
        monkeypatch.setattr('cache_redis.cache.r', redis_session)
        response = get_client.get(f'/post/{post_id}/total_rate',
                                  headers={'Authorization': f'bearer {self.access_token}'})
        assert response.status_code == 200
        assert response.json() == expected_result
