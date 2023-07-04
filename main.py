from typing import Optional
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Cookie, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from auth_backend.authenticate import create_token, get_user_from_token, create_refresh_token, decode_token
from cache_redis.cache import add_rate, show_reviewers, get_rate
from db.db_config import get_db
from db.db_services import create_user, delete_post, update_post, add_post, get_post, get_posts, like_post, \
    remove_like_post, dis_post, remove_dis_post
from models import UserModel, AuthUser, UserModelOutput, PostModel
from auth_backend.authenticate import authenticate
from utils.dependencies import is_owner, get_user_by_token, check_like, check_dislike, check_like_for_del, \
    check_dis_for_del
from utils.paginations import Paginator

app = FastAPI(title='service')
post_rout = APIRouter(prefix='/post')


@app.post('/login/token')
async def authentication(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                         db: AsyncSession = Depends(get_db)) -> dict:
    data = {"email": form_data.username, "password": form_data.password}
    user = AuthUser(**data)
    check = await authenticate(user, db)
    if check[0]:
        access_token = create_token({"sub": form_data.username})
        refresh_token, expire = create_refresh_token({"sub": form_data.username})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=check[1],
            headers={"WWW-Authenticate": "Bearer"}
        )
    expires_str = expire.strftime("%Y-%m-%d %H:%M:%S.%f")
    response.set_cookie(key='refresh_token', httponly=True, value=refresh_token, expires=expires_str)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post('/logout')
async def logout(response: Response) -> Response:
    response.delete_cookie(key='refresh_token')
    return Response(status_code=status.HTTP_200_OK)


@app.post('/reg')
async def register(data: UserModel, db: AsyncSession = Depends(get_db)) -> UserModelOutput:
    new_user = await create_user(data, db)
    return new_user


@app.post('/refresh')
async def refresh_token(refresh_token: str = Cookie(None)) -> dict:
    try:
        payload = decode_token(refresh_token)
    except (JWTError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )
    access_token = create_token(payload)
    return {"access_token": access_token, "token_type": "bearer"}


@post_rout.get('')
async def read_posts(token: str = Depends(get_user_from_token), db: AsyncSession = Depends(get_db),
                     pagination: Paginator = Depends(Paginator)) -> list[dict]:
    posts_list = await get_posts(db, *pagination)
    if not posts_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posts does'\t exists"
        )
    return posts_list


@post_rout.get('/{post_id}')
async def read_post(post_id: int, token: str = Depends(get_user_from_token),
                    db: AsyncSession = Depends(get_db)) -> dict:
    post = await get_post(post_id, db)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} does'\t exists"
        )
    return post


@post_rout.post('')
async def new_post(data: PostModel, user_id: str = Depends(get_user_by_token),
                   token: str = Depends(get_user_from_token), db: AsyncSession = Depends(get_db)) -> Response:
    data.owner_id = user_id
    await add_post(data, db)
    return Response(status_code=status.HTTP_200_OK)


@post_rout.put('/{post_id}')
async def modify_post(post_id: int, data: PostModel, token: str = Depends(get_user_from_token),
                      owner: str = Depends(is_owner), db: AsyncSession = Depends(get_db)) -> Response:
    user_id, is_admin = owner
    if is_admin:
        data.modify_id = user_id
    else:
        data.owner_id = user_id
    await update_post(post_id, data, db)
    return Response(status_code=status.HTTP_200_OK)


@post_rout.delete('/{post_id}')
async def remove_post(post_id: int, token: str = Depends(get_user_from_token),
                      owner: str = Depends(is_owner), db: AsyncSession = Depends(get_db)) -> Response:
    await delete_post(post_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@post_rout.post('/{post_id}/like')
async def add_like(post_id: int, token: str = Depends(get_user_from_token),
                   like: Optional[str] = Depends(check_like), db: AsyncSession = Depends(get_db)) -> dict:
    if like:
        total_likes = await like_post(db, like, post_id)
        return {post_id: total_likes}


@post_rout.delete('/{post_id}/like')
async def remove_like(post_id: int, token: str = Depends(get_user_from_token),
                      check_for_del: Optional[str] = Depends(check_like_for_del),
                      db: AsyncSession = Depends(get_db)) -> dict:
    if check_for_del:
        total_likes = await remove_like_post(db, check_for_del, post_id)
        return {post_id: total_likes}


@post_rout.post('/{post_id}/dis')
async def add_dis(post_id: int, token: str = Depends(get_user_from_token),
                  dis: Optional[str] = Depends(check_dislike), db: AsyncSession = Depends(get_db)) -> dict:
    if dis:
        total_likes = await dis_post(db, dis, post_id)
        return {post_id: total_likes}


@post_rout.delete('/{post_id}/dis')
async def remove_dis(post_id: int, token: str = Depends(get_user_from_token),
                     check_for_del: Optional[str] = Depends(check_dis_for_del),
                     db: AsyncSession = Depends(get_db)) -> dict:
    if check_for_del:
        total_likes = await remove_dis_post(db, check_for_del, post_id)
        return {post_id: total_likes}


@post_rout.get('/{post_id}/total_rate')
async def show_like(post_id: int, token: str = Depends(get_user_from_token)) -> dict:
    return {
        'total_likes': get_rate('likes', post_id),
        'user_set_likes': show_reviewers('likes', post_id),
        'total_dislikes': get_rate('dis', post_id),
        'user_set_dislikes': show_reviewers('dis', post_id),
            }


app.include_router(post_rout)

if __name__ == '__main__':
    uvicorn.run('main:app', port=8000, host='0.0.0.0', reload=True)
