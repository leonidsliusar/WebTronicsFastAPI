from typing import Optional

from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth_backend.authenticate import decode_token
from cache_redis.cache import add_rate, check_exists_rate, remove_rate
from db.db_config import get_db
from db.db_services import UserManager, PostManager
from models import UserToken

already_liked = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Already liked"
)
already_disliked = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Already disliked"
)

post_owner = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="You couldn\'t rate your own posts"
)

do_not_liked_bef = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=f"You haven\'t liked it before'\t exists"
)
do_not_dis_bef = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=f"You haven\'t disliked it before'\t exists"
)


async def is_owner(token: dict, post_id: int, db: AsyncSession) -> tuple[str, bool]:
    email = token.get('email')
    user = await UserManager(db).get(UserToken(email=email))
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if not user.get('user_id') == post.get('owner_id') and not user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You haven\'t permission for modify {post_id}"
        )
    return user.get('user_id'), user.get('is_admin')


async def get_user_by_token(token: str, db: AsyncSession = Depends(get_db)) -> str:
    payload = decode_token(token)
    email = payload.get('sub')
    user = await UserManager(db).get(UserToken(email=email))
    return user.get('user_id')


async def check_like(user: dict, post_id: int, db: AsyncSession) -> Optional[str]:
    email = user.get('email')
    user = await UserManager(db).get(UserToken(email=email))
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if user.get('user_id') == post.get('owner_id'):  # owner of post
        raise post_owner
    already_dis = check_exists_rate('dis', post_id, email)
    if already_dis:
        raise already_disliked
    added = add_rate('likes', post_id, email)  # already liked
    if not added:
        raise already_liked
    return email


async def check_dislike(user: dict, post_id: int, db: AsyncSession) -> Optional[str]:
    email = user.get('email')
    user = await UserManager(db).get(UserToken(email=email))
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if user.get('user_id') == post.get('owner_id'):  # owner of post
        raise post_owner
    already_like = check_exists_rate('likes', post_id, email)
    if already_like:
        raise already_liked
    added = add_rate('dis', post_id, email)  # already disliked
    if not added:
        raise already_disliked
    return email


async def check_like_for_del(user: dict, post_id: int, db: AsyncSession = Depends(get_db)) -> Optional[str]:
    email = user.get('email')
    user = await UserManager(db).get(UserToken(email=email))
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if user.get('user_id') == post.get('owner_id'):  # owner of post
        raise post_owner
    already_like = check_exists_rate('likes', post_id, email)
    if not already_like:
        raise do_not_liked_bef
    remove_rate('likes', post_id, email)
    return email


async def check_dis_for_del(user: dict, post_id: int, db: AsyncSession = Depends(get_db)) -> Optional[str]:
    email = user.get('email')
    user = await UserManager(db).get(UserToken(email=email))
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} doesn'\t exists"
        )
    if user.get('user_id') == post.get('owner_id'):  # owner of post
        raise post_owner
    already_dis = check_exists_rate('dis', post_id, email)
    if not already_dis:
        raise do_not_dis_bef
    remove_rate('dis', post_id, email)
    return email
