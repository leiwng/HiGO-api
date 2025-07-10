# /app/api/v1/endpoints/login.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core import security
from app.core.config import settings
from app.models.token import Token
from app.models.user import User
from app.services.external.fake_user_service import fake_users_db, get_user

router = APIRouter()

def authenticate_user(db, username: str, password: str) -> User | None:
    user_dict = get_user(db, username)
    if not user_dict:
        return None
    # In a real app, you'd have hashed passwords
    if user_dict["password"] != password:
        return None
    return User(**user_dict)


@router.post("/token", response_model=Token, summary="获取认证Token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2兼容的token登录，使用用户名和密码获取访问token。
    """
    # In a real app, you would look up the user in a database
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
