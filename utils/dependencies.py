from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth_backend.authenticate import decode_token
from db.db_config import get_db
from db.db_services import get_user, get_post
from models import UserToken


async def is_owner(token: str, post_id: int, db: AsyncSession = Depends(get_db)) -> tuple[str, bool]:
    payload = decode_token(token)
    email = payload.get('sub')
    user = await get_user(UserToken(email=email), db)
    post = await get_post(post_id, db)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if not user.get('user_id') == post.get('owner_id') and not user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You haven\'t permission for delete {post_id}"
        )
    return user.get('user_id'), user.get('is_admin')


async def get_user_by_token(token: str, db: AsyncSession = Depends(get_db)) -> str:
    payload = decode_token(token)
    email = payload.get('sub')
    user = await get_user(UserToken(email=email), db)
    return user.get('user_id')
