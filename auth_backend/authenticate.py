from fastapi.security import OAuth2PasswordBearer

from db.db_config import get_db
from utils.hasher import check_hash
from datetime import timedelta, datetime
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from db.db_services import get_user
from models import AuthUser, UserToken
from jose import JWTError, jwt
from settings import token_conf

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/token")


async def authenticate(data: AuthUser, db: AsyncSession) -> tuple[bool, str]:
    user = await get_user(data, db)
    if user:
        flag = check_hash(data.password, user.get('password'))
        return flag, 'Ok' if flag else 'Invalid password'
    else:
        return False, 'Invalid email'


def create_token(data: dict,
                 tlc: timedelta = timedelta(minutes=token_conf.get('ACCESS_TOKEN_EXPIRE_MINUTES', 15))) -> str:
    to_encode = data.copy().copy()
    expire = datetime.utcnow() + tlc
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, token_conf.get('SECRET_KEY'), algorithm=token_conf.get('ALGORITHM', 'HS256'))
    return encoded_jwt


def decode_token(token: str):
    payload = jwt.decode(token, token_conf.get('SECRET_KEY'), algorithms=token_conf.get('ALGORITHM', 'HS256'))
    return payload


async def get_user_from_token(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email = payload.get('sub')
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = UserToken(email=email)
    user_data = await get_user(user, db)
    if not user_data:
        raise credentials_exception
    user_data.pop('password')
    return user_data
