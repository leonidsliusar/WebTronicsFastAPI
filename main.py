import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth_backend.authenticate import create_token, get_user_from_token
from db.db_config import get_db
from db.db_services import create_user
from models import UserModel, AuthUser, UserModelOutput
from auth_backend.authenticate import authenticate

app = FastAPI(title='service')


@app.post('/login/token')
async def auth(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    data = {"email": form_data.username, "password": form_data.password}
    user = AuthUser(**data)
    check = await authenticate(user, db)
    if check[0]:
        access_token = create_token({"sub": form_data.username})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=check[1],
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post('/reg')
async def reg(data: UserModel, db: AsyncSession = Depends(get_db)) -> UserModelOutput:
    new_user = await create_user(data, db)
    return new_user


@app.get('/test')
async def foo(data: str = Depends(get_user_from_token)):
    pass


if __name__ == '__main__':
    uvicorn.run(app)
