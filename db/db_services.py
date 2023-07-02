from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_schema import User
from models import UserModel, UserModelOutput
from utils.hasher import hash_pass


async def create_user(user: UserModel, db: AsyncSession) -> UserModelOutput:
    user.password = hash_pass(user.password)
    query = insert(User).values(user.dict()).returning(User.user_id, User.first_name, User.last_name, User.email)
    returning_result = await db.execute(query)
    user_data = returning_result.fetchone()._mapping
    return UserModelOutput(**user_data)
