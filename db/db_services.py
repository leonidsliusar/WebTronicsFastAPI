from typing import Union
from sqlalchemy import insert, select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_schema import User, Post, Like, Dislike
from models import UserModel, UserModelOutput, AuthUser, UserToken, PostModel
from utils.hasher import hash_pass


async def create_user(user: UserModel, db: AsyncSession) -> UserModelOutput:
    user_to_inset = user.copy()
    user_to_inset.password = hash_pass(user.password)
    query = insert(User).values(user_to_inset.dict()).returning(
        User.user_id, User.first_name, User.last_name, User.email)
    returning_result = await db.execute(query)
    user_data = returning_result.mappings().fetchone()
    return UserModelOutput(**user_data)


async def get_user(user: Union[AuthUser, UserToken], db: AsyncSession) -> dict:
    query = select(User).where(User.email == user.email)
    returning_result = await db.execute(query)
    user_data = returning_result.scalar()
    user_dict = {}
    if user_data:
        user_dict.update(user_data.__dict__)
        user_dict.pop('_sa_instance_state', None)
    return user_dict


async def get_posts(db: AsyncSession, page: int, limit: int) -> list[dict]:
    offset = page * limit + 1
    query = select(Post).limit(limit=limit).offset(offset=offset)
    returning_result = await db.execute(query)
    posts = returning_result.all()
    posts_lists = [post.__dict__ for post in posts] if posts else []
    return posts_lists


async def get_post(post_id: int, db: AsyncSession) -> dict:
    query = select(Post).where(post_id=post_id)
    returning_result = await db.execute(query)
    if not returning_result:
        return {}
    post = returning_result.scalar()
    post_dict = {}
    if post:
        post_dict.update(post.__dict__)
    return post_dict


async def add_post(post: PostModel, db: AsyncSession) -> None:
    query = insert(Post).values(**post.dict())
    await db.execute(query)


async def update_post(post_id: id, data: PostModel, db: AsyncSession) -> None:
    query = update(Post).values(**data.dict()).where(post_id=post_id)
    await db.execute(query)


async def delete_post(post_id: int, db: AsyncSession) -> None:
    query = delete(Post).where(Post.post_id == post_id)
    await db.execute(query)


async def like_post(db: AsyncSession, email: str, post_id: int) -> int:
    query = insert(Like).values(post_id=post_id, reviewer=email)
    await db.execute(query)
    query = select(func.count(Like.rate_id)).join(Post).where(Post.post_id == post_id)
    row_likes_for_post = await db.execute(query)
    likes_for_post = row_likes_for_post.scalar()
    return likes_for_post


async def dis_post(db: AsyncSession, email: str, post_id: int) -> int:
    query = insert(Dislike).values(post_id=post_id, reviewer=email)
    await db.execute(query)
    query = select(func.count(Dislike.rate_id)).join(Post).where(Post.post_id == post_id)
    row_dis_for_post = await db.execute(query)
    dis_for_post = row_dis_for_post.scalar()
    return dis_for_post


async def remove_like_post(db: AsyncSession, email: str, post_id: int) -> int:
    query = delete(Like).where(post_id=post_id, reviewer=email)
    await db.execute(query)
    query = select(func.count(Like.rate_id)).join(Post).where(Post.post_id == post_id)
    row_likes_for_post = await db.execute(query)
    likes_for_post = row_likes_for_post.scalar()
    return likes_for_post


async def remove_dis_post(db: AsyncSession, email: str, post_id: int) -> int:
    query = delete(Dislike).where(post_id=post_id, reviewer=email)
    await db.execute(query)
    query = select(func.count(Dislike.rate_id)).join(Post).where(Post.post_id == post_id)
    row_dis_for_post = await db.execute(query)
    dis_for_post = row_dis_for_post.scalar()
    return dis_for_post
