import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_config import get_db
from db.db_services import create_user
from models import UserModel

app = FastAPI(title='service')


@app.post('/auth')
async def auth(data: UserModel):
    return data


@app.post('/reg')
async def reg(data: UserModel, db: AsyncSession = Depends(get_db)):
    new_user = await create_user(data, db)
    return new_user


if __name__ == '__main__':
    uvicorn.run(app)
