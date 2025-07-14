# /app/api/v1/endpoints/chat.py
from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.security import get_current_active_user
from app.models.chat import TextChatRequest, ImageChatRequest, ChatRequest, ChatResponse
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.external.llm_service import LLMService
from app.services.storage.mongo_service import MongoService
from app.services.storage.redis_service import RedisService
from app.models.api_key import APIKey
from app.services.api_key_service import APIKeyService
from app.core.api_key_auth import get_current_api_key
from app.core.logging import get_logger

logger = get_logger(__name__)
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


class OpenAIChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str

class OpenAIChatRequest(BaseModel):
    """OpenAI兼容的聊天请求格式"""
    model: str = Field(default="gpt-3.5-turbo")
    messages: list[OpenAIChatMessage]
    max_tokens: int | None = Field(None, ge=1, le=4000)
    temperature: float = Field(0.7, ge=0, le=2)
    stream: bool = False

class OpenAIChatResponse(BaseModel):
    """OpenAI兼容的聊天响应格式"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict

@router.post("/completions", response_model=OpenAIChatResponse, summary="Chat Completions (OpenAI Compatible)")
async def chat_completions(
    request: Request,
    chat_request: OpenAIChatRequest,
    api_key: APIKey = Depends(get_current_api_key)
):
    """
    OpenAI兼容的聊天完成API
    """
    chat_service = ChatService()
    api_key_service = APIKeyService()

    try:
        # 预估Token使用量
        estimated_tokens = len(" ".join([msg.content for msg in chat_request.messages])) // 4

        # 检查配额
        await api_key_service.check_quota(api_key, estimated_tokens)

        # 转换为内部格式
        conversation_id = f"api_{api_key.id}_{int(datetime.now(timezone.utc).timestamp())}"

        # 构建对话内容
        messages_text = "\n".join([f"{msg.role}: {msg.content}" for msg in chat_request.messages])

        internal_request = ChatRequest(
            question=messages_text,
            conversation_id=conversation_id,
            context={
                "model": chat_request.model,
                "temperature": chat_request.temperature,
                "max_tokens": chat_request.max_tokens
            }
        )

        # 处理聊天请求
        chat_response = await chat_service.process_chat_request(internal_request)

        if not chat_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=chat_response.error
            )

        # 计算实际使用的Token
        prompt_tokens = len(messages_text) // 4
        completion_tokens = len(chat_response.response) // 4
        total_tokens = prompt_tokens + completion_tokens

        # 记录使用量
        await api_key_service.record_usage(api_key, {
            "endpoint": "/chat/completions",
            "method": "POST",
            "model": chat_request.model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        })

        # 构建OpenAI兼容的响应
        response_id = f"chatcmpl-{conversation_id}"

        return OpenAIChatResponse(
            id=response_id,
            created=int(datetime.now(timezone.utc).timestamp()),
            model=chat_request.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": chat_response.response
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# 保留原有的聊天端点用于向后兼容
@router.post("/", response_model=ChatResponse, summary="发送聊天消息")
async def chat(
    request: ChatRequest,
    api_key: APIKey = Depends(get_current_api_key)
):
    """
    原有的聊天API (保持向后兼容)
    """
    chat_service = ChatService()
    api_key_service = APIKeyService()

    try:
        # 预估Token使用量
        estimated_tokens = len(request.question) // 4

        # 检查配额
        await api_key_service.check_quota(api_key, estimated_tokens)

        # 处理聊天请求
        response = await chat_service.process_chat_request(request)

        if response.success:
            # 计算实际使用的Token
            prompt_tokens = len(request.question) // 4
            completion_tokens = len(response.response) // 4
            total_tokens = prompt_tokens + completion_tokens

            # 记录使用量
            await api_key_service.record_usage(api_key, {
                "endpoint": "/chat",
                "method": "POST",
                "model": "default",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            })

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服务错误: {str(e)}"
        )
