# /app/api/v1/api.py
from fastapi import APIRouter, Depends

from app.api.v1.endpoints import chat, login, api_keys
from app.services.external.multimodal_service import get_multimodal_service, MultiModalService
from app.models.chat import ImageAnalysisRequest  # 添加这个导入

api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(login.router, prefix="/auth", tags=["认证"])
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])
api_router.include_router(api_keys.router, prefix="/account", tags=["账户管理"])


@api_router.post("/analyze-image")
async def analyze_image(
    image_data: ImageAnalysisRequest,
    multimodal_service: MultiModalService = Depends(get_multimodal_service),
):
    result = await multimodal_service.analyze_image(
        image_data.image_base64, image_data.image_type, image_data.pet_info
    )
    return result
