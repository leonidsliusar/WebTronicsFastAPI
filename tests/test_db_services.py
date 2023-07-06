import uuid

import pytest
from sqlalchemy import insert, select

from db.db_schema import Post, Like, Dislike
from db.db_services import UserManager, PostManager
from models import UserModel, UserModelOutput, AuthUser, UserToken, PostModel, UpdatePostModel


async def test_create_user(setup_and_teardown_db):
    user = UserModel(
        first_name='firstname',
        last_name='lastname',
        password='Qwerty1234',
        email='foo@example.com'
    )
    session = setup_and_teardown_db
    async with session:
        user_to_client = await UserManager(session).create(user)
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
        manager = UserManager(session)
        await manager.create(user)
        fetch_user = AuthUser(
            email='foo@example.com',
            password='Qwerty1234'
        )
        user_data = await manager.get(fetch_user)
    assert isinstance(user_data, dict)
    assert user_data.get('email') == user.email
    assert user_data.get('first_name') == user.first_name
    assert user_data.get('last_name') == user.last_name
    assert isinstance(user_data.get('user_id'), uuid.UUID)


async def test_get_posts_many(setup_and_teardown_db, stub_user_posts):
    session = setup_and_teardown_db
    result = await PostManager(session).get_many()
    assert len(result) == 10


@pytest.mark.parametrize('page, limit, expected_len, expected_check',
                         [
                             (0, 10, 10, 1),
                             (1, 5, 4, 7),
                             (2, 2, 2, 6),
                             (8, 1, 1, 10)
                         ]
                         )
async def test_get_posts_many_filter(setup_and_teardown_db, stub_user_posts, page, limit, expected_len, expected_check):
    session = setup_and_teardown_db
    result = await PostManager(session).get_many_filter(page, limit)
    assert result[0].get('post_id') == expected_check
    assert len(result) == expected_len


async def test_get_post(setup_and_teardown_db, stub_user_posts):
    session = setup_and_teardown_db
    post = await PostManager(session).get(1)
    assert post.get('post_id') == 1


async def test_create_post(setup_and_teardown_db, get_stub_user):
    user = get_stub_user
    session = setup_and_teardown_db
    user = await UserManager(session).create(user)
    manager = PostManager(session)
    user_id = user.user_id
    post = PostModel(
        title='test title',
        owner_id=user_id,
        modify_id=user_id,
        content='test content'
    )
    post_id = await manager.create(post)
    post = await manager.get(post_id)
    assert post.get('owner_id') == user_id


async def test_update_post(setup_and_teardown_db, stub_user_posts):
    session = setup_and_teardown_db
    post_before = await session.execute(select(Post.content).where(Post.post_id == 1))
    content_before = post_before.scalar()[0]
    data = {'content': 'new content'}
    data = UpdatePostModel(**data)
    await PostManager(session).update(1, data)
    post_after = await session.execute(select(Post.content).where(Post.post_id == 1))
    content_after = post_after.scalar()[0]
    assert content_after != content_before


async def test_delete_post(setup_and_teardown_db, stub_user_posts):
    session = setup_and_teardown_db
    post = await session.execute(select(Post.content).where(Post.post_id == 1))
    assert post.scalar()
    await PostManager(session).delete(1)
    post = await session.execute(select(Post.content).where(Post.post_id == 1))
    assert not post.scalar()


async def test_add_like(setup_and_teardown_db, stub_user_posts, add_stub_user):
    session = setup_and_teardown_db
    query = select(Like).where(Like.post_id == 1)
    like = await session.execute(query)
    likes = like.scalars()
    assert [like.reviewer for like in likes] == []
    total = await PostManager(session).add_like('foo@example.com', 1)
    assert total == 1
    like = await session.execute(query)
    likes = like.scalars()
    assert [like.reviewer for like in likes] == ['foo@example.com']


async def test_add_dis(setup_and_teardown_db, stub_user_posts, add_stub_user):
    session = setup_and_teardown_db
    query = select(Dislike).where(Dislike.post_id == 1)
    dis = await session.execute(query)
    dislikes = dis.scalars()
    assert [dis.reviewer for dis in dislikes] == []
    total = await PostManager(session).add_dis('foo@example.com', 1)
    assert total == 1
    dis = await session.execute(query)
    dislikes = dis.scalars()
    assert [dis.reviewer for dis in dislikes] == ['foo@example.com']


async def test_remove_like(setup_and_teardown_db, stub_user_posts, add_stub_user):
    session = setup_and_teardown_db
    query = insert(Like).values(post_id=1, reviewer='foo@example.com')
    await session.execute(query)
    query = select(Like).where(Like.post_id == 1)
    like = await session.execute(query)
    likes = like.scalars()
    assert [like.reviewer for like in likes] == ['foo@example.com']
    total = await PostManager(session).remove_like('foo@example.com', 1)
    assert total == 0
    like = await session.execute(query)
    likes = like.scalars()
    assert [like.reviewer for like in likes] == []


async def test_remove_dis(setup_and_teardown_db, stub_user_posts, add_stub_user):
    session = setup_and_teardown_db
    query = insert(Dislike).values(post_id=1, reviewer='foo@example.com')
    await session.execute(query)
    query = select(Dislike).where(Dislike.post_id == 1)
    dis = await session.execute(query)
    dislikes = dis.scalars()
    assert [dis.reviewer for dis in dislikes] == ['foo@example.com']
    total = await PostManager(session).remove_dis('foo@example.com', 1)
    assert total == 0
    dis = await session.execute(query)
    dislikes = dis.scalars()
    assert [dis.reviewer for dis in dislikes] == []
