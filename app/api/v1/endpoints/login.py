# /app/api/v1/endpoints/login.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core import security
from app.core.config import settings
from app.core.rate_limiter import LoginRateLimiter
from app.models.token import Token
from app.models.user import User
from app.services.external.user_service import UserService
from app.services.storage.mongo_service import MongoService
from app.services.storage.redis_service import RedisService
from app.utils.password_validator import PasswordValidator

router = APIRouter()

# 添加用户注册的请求模型
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str = None

async def get_user_service() -> UserService:
    """依赖注入用户服务"""
    mongo_service = MongoService()
    return UserService(mongo_service)

async def get_rate_limiter() -> LoginRateLimiter:
    redis_service = RedisService()
    return LoginRateLimiter(redis_service)

@router.post("/token", response_model=Token, summary="获取认证Token")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
    rate_limiter: LoginRateLimiter = Depends(get_rate_limiter)
):
    """
    OAuth2兼容的token登录，使用用户名和密码获取访问token。
    """
    # 获取客户端IP作为限制标识
    client_ip = request.client.host
    identifier = f"{client_ip}:{form_data.username}"

    # 检查速率限制
    if not await rate_limiter.check_rate_limit(identifier):
        # 获取锁定详细信息
        lockout_info = await rate_limiter.get_lockout_info(identifier)
        remaining_minutes = lockout_info["remaining_seconds"] // 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试次数过多，请在{remaining_minutes}分钟后再试"
        )

    # 验证用户
    user = await user_service.authenticate_user(
        form_data.username,
        form_data.password
    )

    if not user:
        # 记录失败尝试
        await rate_limiter.record_failed_attempt(identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # 登录成功，清除尝试记录
    await rate_limiter.clear_attempts(identifier)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/register", response_model=dict, summary="用户注册")
async def register_user(
    user_data: UserRegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    注册新用户
    """
    try:
        user = await user_service.create_user(
            user_data.username,
            user_data.password,
            user_data.email
        )
        return {
            "success": True,
            "message": "用户注册成功",
            "data": {
                "username": user.username,
                "email": user.email
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/password-requirements", summary="获取密码要求")
async def get_password_requirements():
    """
    获取密码复杂度要求
    """
    return PasswordValidator.get_requirements()

@router.post("/validate-password", summary="验证密码强度")
async def validate_password(password: str):
    """
    验证密码是否符合要求，用于前端实时验证
    """
    is_valid, errors = PasswordValidator.validate(password)
    return {
        "valid": is_valid,
        "errors": errors,
        "requirements": PasswordValidator.get_requirements()
    }
