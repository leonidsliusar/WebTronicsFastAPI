from fastapi.security import OAuth2PasswordBearer

from settings import settings
from db.db_config import get_db
from utils.hasher import check_hash
from datetime import timedelta, datetime
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from db.db_services import UserManager
from models import AuthUser, UserToken
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/token")


async def authenticate(data: AuthUser, db: AsyncSession) -> tuple[bool, str]:
    manager = UserManager(db)
    user = await manager.get(data)
    if user:
        flag = check_hash(data.password, user.get('password'))
        return flag, 'Ok' if flag else 'Invalid password'
    else:
        return False, 'Invalid email'


def create_token(data: dict,
                 tlc: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + tlc
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict,
                         tlc: timedelta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRES_IN)) -> tuple[str, datetime]:
    to_encode = data.copy()
    expire = datetime.utcnow() + tlc
    to_encode.update({'exp': expire})
    encoded_jwt_refresh = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt_refresh, expire


def decode_token(token: str):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
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
    manager = UserManager(db)
    user_data = await manager.get(user)
    if not user_data:
        raise credentials_exception
    user_data.pop('password')
    return user_data
