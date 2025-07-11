# /app/api/v1/endpoints/chat.py
import time
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.security import get_current_active_user
from app.models.chat import TextChatRequest, ImageChatRequest, ImageType, ChatRequest, ChatResponse
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.external.llm_service import LLMService
from app.services.storage.mongo_service import MongoService
from app.services.storage.redis_service import RedisService

router = APIRouter()


async def get_chat_service() -> ChatService:
    """依赖注入聊天服务"""
    llm_service = LLMService()
    mongo_service = MongoService()
    redis_service = RedisService()
    return ChatService(llm_service, mongo_service, redis_service)


@router.post("/text", summary="文本咨询API")
async def chat_text(
    request: TextChatRequest,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(),
):
    """
    处理文本聊天请求，流式返回响应。
    """
    request_id = f"{current_user.id}-{int(time.time() * 1000)}"
    logger.info(f"Request ID: {request_id} - Received text chat request from user: {current_user.id}")

    try:
        response_stream = chat_service.process_text_chat(
            request=request, user=current_user, request_id=request_id
        )
        return StreamingResponse(
            response_stream,
            media_type="text/event-stream",
            headers={
                "Content-Type": "text/event-stream; charset=utf-8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id,
            },
        )
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error processing text chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/image", summary="图片咨询API")
async def chat_image(
    request: ImageChatRequest,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(),
):
    """
    处理图像聊天请求，流式返回响应。
    """
    request_id = f"{current_user.id}-{int(time.time() * 1000)}"
    logger.info(f"Request ID: {request_id} - Received image chat request from user: {current_user.id}")

    if not request.images:
        raise HTTPException(status_code=400, detail="Images list cannot be empty.")

    if len(request.images) > 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 images allowed.")

    try:
        response_stream = chat_service.process_image_chat(
            request=request, user=current_user, request_id=request_id
        )
        return StreamingResponse(
            response_stream,
            media_type="text/event-stream",
            headers={
                "Content-Type": "text/event-stream; charset=utf-8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id,
            },
        )
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error processing image chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse, summary="发送聊天消息")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    发送聊天消息并获取AI回复
    """
    try:
        response = await chat_service.process_chat_request(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服务错误: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/history", response_model=list[dict], summary="获取对话历史")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 10,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取指定对话的历史记录
    """
    try:
        history = await chat_service.get_conversation_history(conversation_id, limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in history
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )
