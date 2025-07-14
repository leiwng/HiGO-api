# /app/models/token.py
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: str
    scopes: list[str] = []
