from abc import ABC, abstractmethod
from typing import Union
from sqlalchemy import insert, select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_schema import User, Post, Like, Dislike
from models import UserModel, UserModelOutput, AuthUser, UserToken, PostModel, UpdatePostModel
from utils.hasher import hash_pass


class BaseManager(ABC):
    __slots__ = 'db'

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def create(self, *args, **kwargs):
        pass

    @abstractmethod
    async def get(self, *args, **kwargs):
        pass


class UserManager(BaseManager):

    async def create(self, user: UserModel) -> UserModelOutput:
        user_to_inset = user.copy()
        user_to_inset.password = hash_pass(user.password)
        query = insert(User).values(user_to_inset.dict()).returning(
            User.user_id, User.first_name, User.last_name, User.email)
        returning_result = await self.db.execute(query)
        user_data = returning_result.mappings().fetchone()
        return UserModelOutput(**user_data)

    async def get(self, user: Union[AuthUser, UserToken]) -> dict:
        query = select(User).where(User.email == user.email)
        returning_result = await self.db.execute(query)
        user_data = returning_result.scalar()
        user_dict = {}
        if user_data:
            user_dict.update(user_data.__dict__)
            user_dict.pop('_sa_instance_state', None)
        return user_dict


class PostManager(BaseManager):

    async def create(self, post: PostModel) -> int:
        query = insert(Post).values(**post.dict()).returning(Post.post_id)
        post_id = await self.db.execute(query)
        return post_id.fetchone()[0]

    async def get(self, post_id: int) -> dict:
        query = select(Post).where(Post.post_id == post_id)
        returning_result = await self.db.execute(query)
        if not returning_result:
            return {}
        post = returning_result.scalar()
        post_dict = {}
        if post:
            post_dict.update(post.__dict__)
            post_dict.pop('_sa_instance_state')
        return post_dict

    async def get_many(self) -> list[dict]:
        query = select(Post)
        returning_result = await self.db.execute(query)
        posts = returning_result.scalars()
        if posts:
            posts_list = [post.__dict__ for post in posts]
            for x in posts_list:
                x.pop('_sa_instance_state', None)
        else:
            posts_list = []
        return posts_list

    async def get_many_filter(self, page: int, limit: int) -> list[dict]:
        if page:
            offset = page * limit + 1
        else:
            offset = 0
        query = select(Post).limit(limit).offset(offset)
        returning_result = await self.db.execute(query)
        posts = returning_result.scalars()
        if posts:
            posts_list = [post.__dict__ for post in posts]
            for x in posts_list:
                x.pop('_sa_instance_state', None)
        else:
            posts_list = []
        return posts_list

    async def update(self, post_id: id, data: PostModel) -> None:
        data_dict = {key: value for key, value in data.dict().items() if value}
        query = update(Post).where(Post.post_id == post_id).values(**data_dict)
        await self.db.execute(query)

    async def delete(self, post_id: int) -> None:
        query = delete(Post).where(Post.post_id == post_id)
        await self.db.execute(query)

    async def add_like(self, email: str, post_id: int) -> int:
        query = insert(Like).values(post_id=post_id, reviewer=email)
        await self.db.execute(query)
        query = select(func.count(Like.rate_id)).join(Post).where(Post.post_id == post_id)
        row_likes_for_post = await self.db.execute(query)
        likes_for_post = row_likes_for_post.scalar()
        return likes_for_post

    async def remove_like(self, email: str, post_id: int) -> int:
        query = delete(Like).where(Like.post_id == post_id, Like.reviewer == email)
        await self.db.execute(query)
        query = select(func.count(Like.rate_id)).join(Post).where(Post.post_id == post_id)
        row_likes_for_post = await self.db.execute(query)
        likes_for_post = row_likes_for_post.scalar()
        return likes_for_post

    async def add_dis(self, email: str, post_id: int) -> int:
        query = insert(Dislike).values(post_id=post_id, reviewer=email)
        await self.db.execute(query)
        query = select(func.count(Dislike.rate_id)).join(Post).where(Post.post_id == post_id)
        row_dis_for_post = await self.db.execute(query)
        dis_for_post = row_dis_for_post.scalar()
        return dis_for_post

    async def remove_dis(self, email: str, post_id: int) -> int:
        query = delete(Dislike).where(Dislike.post_id == post_id, Dislike.reviewer == email)
        await self.db.execute(query)
        query = select(func.count(Dislike.rate_id)).join(Post).where(Post.post_id == post_id)
        row_dis_for_post = await self.db.execute(query)
        dis_for_post = row_dis_for_post.scalar()
        return dis_for_post
