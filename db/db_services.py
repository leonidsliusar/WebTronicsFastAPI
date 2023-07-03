from typing import Union

from sqlalchemy import insert, select, Result
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_schema import User
from models import UserModel, UserModelOutput, AuthUser, UserToken
from utils.hasher import hash_pass


async def create_user(user: UserModel, db: AsyncSession) -> UserModelOutput:
    user_to_inset = user.copy()
    user_to_inset.password = hash_pass(user.password)
    query = insert(User).values(user_to_inset.dict()).returning(User.user_id, User.first_name, User.last_name, User.email)
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
