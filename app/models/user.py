# /app/models/user.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: str | None = None
    username: str
    email: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str | None = None

class UserUpdate(BaseModel):
    email: str | None = None
    is_active: bool | None = None

class UserInDB(User):
    password_hash: str
    salt: str
