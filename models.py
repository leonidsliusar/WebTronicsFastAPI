import re
import uuid
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, validator, Field, EmailStr


class UserModel(BaseModel):
    first_name: str = Field(max_length=35, regex=r'^[a-zA-Z]+$')
    last_name: str = Field(max_length=35, regex=r'^[a-zA-Z]+$')
    password: str = Field()
    email: EmailStr

    @validator('password', pre=True)
    def validate_password(cls, password):
        pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])[A-Za-z\d]{8,}$'
        if re.match(pattern, password):
            return password
        else:
            raise ValueError(
                'The password isn\'t strong enough:\nMinimum eight characters, at least one uppercase latin letter, '
                'one lowercase latin letter and one number'
            )


class UserModelOutput(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr


user_data = {
        "user_id": uuid.uuid4(),
        "first_name": 'firstname',
        "last_name": 'lastname',
        "email": "foo@example.com"
    }


class AuthUser(BaseModel):
    email: EmailStr
    password: str


class UserToken(BaseModel):
    email: EmailStr


class PostModel(BaseModel):
    title: str = Field(max_length=60)
    content: str
    owner_id: Optional[UUID]
    modify_id: Optional[UUID]
