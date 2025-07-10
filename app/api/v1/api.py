# /app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import chat, login

api_router = APIRouter()
api_router.include_router(login.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
