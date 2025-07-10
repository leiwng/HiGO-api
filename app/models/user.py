# /app/models/user.py
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
