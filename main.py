from typing import Optional
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Cookie, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from auth_backend.authenticate import create_token, get_user_from_token, create_refresh_token, decode_token
from cache_redis.cache import show_reviewers, get_rate
from db.db_config import get_db
from db.db_services import UserManager, PostManager
from models import UserModel, AuthUser, UserModelOutput, PostModel, UpdatePostModel
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
    new_user = await UserManager(db).create(data)
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


@post_rout.get('/filter')
async def read_posts_filter(token: dict = Depends(get_user_from_token), db: AsyncSession = Depends(get_db),
                     pagination: Paginator = Depends(Paginator)) -> list[dict]:
    posts_list = await PostManager(db).get_many_filter(**pagination.__dict__)
    if not posts_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posts does'\t exists"
        )
    return posts_list


@post_rout.get('')
async def read_posts(token: dict = Depends(get_user_from_token), db: AsyncSession = Depends(get_db)) -> list[dict]:
    posts_list = await PostManager(db).get_many()
    if not posts_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Posts does'\t exists"
        )
    return posts_list


@post_rout.get('/{post_id}')
async def read_post(post_id: int, token: dict = Depends(get_user_from_token),
                    db: AsyncSession = Depends(get_db)) -> dict:
    post = await PostManager(db).get(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} does'\t exists"
        )
    return post


@post_rout.post('')
async def new_post(data: PostModel,
                   token: dict = Depends(get_user_from_token), db: AsyncSession = Depends(get_db)) -> Response:
    user_id = token.get('user_id')
    data.owner_id = user_id
    data.modify_id = user_id
    await PostManager(db).create(data)
    return Response(status_code=status.HTTP_200_OK)


@post_rout.put('/{post_id}')
async def modify_post(post_id: int, data: PostModel, token: dict = Depends(get_user_from_token),
                      db: AsyncSession = Depends(get_db)) -> Response:
    user_id, is_admin = await is_owner(token, post_id, db)
    if is_admin:
        data.modify_id = user_id
    else:
        data.owner_id = user_id
    await PostManager(db).update(post_id, data)
    return Response(status_code=status.HTTP_200_OK)


@post_rout.delete('/{post_id}')
async def remove_post(post_id: int, token: dict = Depends(get_user_from_token),
                      db: AsyncSession = Depends(get_db)) -> Response:
    await is_owner(token, post_id, db)
    await PostManager(db).delete(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@post_rout.post('/{post_id}/like')
async def add_like(post_id: int, token: dict = Depends(get_user_from_token),
                   db: AsyncSession = Depends(get_db)) -> dict:
    email = await check_like(token, post_id, db)
    if email:
        total_likes = await PostManager(db).add_like(email, post_id)
        return {post_id: total_likes}


@post_rout.delete('/{post_id}/like')
async def remove_like(post_id: int, token: dict = Depends(get_user_from_token),
                      db: AsyncSession = Depends(get_db)) -> dict:
    email = await check_like_for_del(token, post_id, db)
    if email:
        total_likes = await PostManager(db).remove_like(email, post_id)
        return {post_id: total_likes}


@post_rout.post('/{post_id}/dis')
async def add_dis(post_id: int, token: dict = Depends(get_user_from_token),
                  db: AsyncSession = Depends(get_db)) -> dict:
    email = await check_dislike(token, post_id, db)
    if email:
        total_dis = await PostManager(db).add_dis(email, post_id)
        return {post_id: total_dis}


@post_rout.delete('/{post_id}/dis')
async def remove_dis(post_id: int, token: dict = Depends(get_user_from_token),
                     db: AsyncSession = Depends(get_db)) -> dict:
    email = await check_dis_for_del(token, post_id, db)
    if email:
        total_dis = await PostManager(db).remove_dis(email, post_id)
        return {post_id: total_dis}


@post_rout.get('/{post_id}/total_rate')
async def show_like(post_id: int, token: dict = Depends(get_user_from_token)) -> dict:
    return {
        'total_likes': get_rate('likes', post_id),
        'user_set_likes': show_reviewers('likes', post_id),
        'total_dislikes': get_rate('dis', post_id),
        'user_set_dislikes': show_reviewers('dis', post_id),
            }


app.include_router(post_rout)

if __name__ == '__main__':
    uvicorn.run('main:app', port=8000, host='0.0.0.0', reload=True)
