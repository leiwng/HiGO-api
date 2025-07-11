# /app/services/chat_service.py
import json
import asyncio
from datetime import datetime
from fastapi import Depends, HTTPException
from loguru import logger

from app.models.chat import TextChatRequest, ImageChatRequest, StreamChunk, ChatRequest, ChatResponse, ChatMessage
from app.models.user import User
from app.services.external.llm_service import LLMService
from app.services.external.multimodal_service import MultiModalService
from app.services.external.pet_info_service import PetInfoService
from app.services.storage.mongo_service import MongoService
from app.services.storage.redis_service import RedisService


class ChatService:
    def __init__(
        self,
        llm_service: LLMService = Depends(),
        multimodal_service: MultiModalService = Depends(),
        pet_info_service: PetInfoService = Depends(),
        mongo_service: MongoService = Depends(),
        redis_service: RedisService = Depends(),
    ):
        self.llm_service = llm_service
        self.multimodal_service = multimodal_service
        self.pet_info_service = pet_info_service
        self.mongo_service = mongo_service
        self.redis_service = redis_service

    async def process_text_chat(self, request: TextChatRequest, user: User, request_id: str):
        """
        处理文本咨询的核心逻辑
        1. 获取宠物信息和对话历史
        2. (模拟)RAG检索
        3. 构建Prompt
        4. 调用LLM
        5. 流式返回并保存历史
        """
        logger.info(f"Request ID: {request_id} - Starting text chat process for conversation: {request.conversation_id}")
        full_response_content = ""
        try:
            # 1. 获取宠物信息和对话历史
            pet_info_task = self.pet_info_service.get_pet_info(request.pet_id)
            history_task = self.mongo_service.get_conversation_history(request.conversation_id)
            pet_info, history = await asyncio.gather(pet_info_task, history_task)

            # 2. (模拟)RAG检索
            rag_knowledge = self._rag_retrieval(request.question)

            # 3. 构建Prompt
            prompt = self._build_prompt(request.question, pet_info, history, rag_knowledge)

            # 4. 调用LLM
            logger.info(f"Request ID: {request_id} - Calling LLM for conversation: {request.conversation_id}")
            llm_stream = self.llm_service.stream_chat(prompt)

            # 5. 流式返回
            async for chunk in llm_stream:
                content_piece = chunk.choices[0].delta.content or ""
                full_response_content += content_piece

                stream_chunk = StreamChunk(
                    conversation_id=request.conversation_id,
                    text_chunk=content_piece,
                    is_final=False,
                    timestamp=datetime.utcnow().isoformat()
                )
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.01) # Small delay to allow client processing

            # 标记流结束
            final_chunk = StreamChunk(
                conversation_id=request.conversation_id,
                text_chunk="",
                is_final=True,
                timestamp=datetime.utcnow().isoformat()
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            logger.info(f"Request ID: {request_id} - Finished streaming response for conversation: {request.conversation_id}")

        except Exception as e:
            logger.error(f"Request ID: {request_id} - Exception during text chat: {e}")
            # Yield a structured error message
            error_message = {
                "success": False,
                "error": "ChatProcessingError",
                "detail": str(e)
            }
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
            # 6. 保存对话历史
            if full_response_content:
                await self.mongo_service.save_message(request.conversation_id, "user", request.question)
                await self.mongo_service.save_message(request.conversation_id, "assistant", full_response_content)
                logger.info(f"Request ID: {request_id} - Saved conversation history for: {request.conversation_id}")


    async def process_image_chat(self, request: ImageChatRequest, user: User, request_id: str):
        """
        处理图片咨询的核心逻辑
        1. 解读图片
        2. 获取宠物信息和对话历史
        3. (模拟)RAG检索
        4. 整合信息构建Prompt
        5. 调用LLM
        6. 流式返回并保存历史
        """
        logger.info(f"Request ID: {request_id} - Starting image chat process for conversation: {request.conversation_id}")
        full_response_content = ""
        try:
            # 1. 获取宠物信息和对话历史
            pet_info_task = self.pet_info_service.get_pet_info(request.pet_id)
            history_task = self.mongo_service.get_conversation_history(request.conversation_id)
            pet_info, history = await asyncio.gather(pet_info_task, history_task)

            # 2. 解读图片
            logger.info(f"Request ID: {request_id} - Analyzing {len(request.images)} image(s) with type '{request.image_type.value}'")
            image_analysis_tasks = [
                self.multimodal_service.analyze_image(
                    image_base64=img,
                    image_type=request.image_type,
                    pet_info=pet_info
                ) for img in request.images
            ]
            analysis_results = await asyncio.gather(*image_analysis_tasks)
            image_descriptions = "\n".join([res['data'][0]['text'] for res in analysis_results if res and res.get('data')])

            if not image_descriptions:
                raise Exception("Failed to analyze images or got empty results.")
            logger.info(f"Request ID: {request_id} - Image analysis complete.")

            # 3. (模拟)RAG检索
            rag_knowledge = self._rag_retrieval(request.question + "\n" + image_descriptions)

            # 4. 整合信息构建Prompt
            prompt = self._build_prompt(request.question, pet_info, history, rag_knowledge, image_descriptions)

            # 5. 调用LLM
            logger.info(f"Request ID: {request_id} - Calling LLM for conversation: {request.conversation_id}")
            llm_stream = self.llm_service.stream_chat(prompt)

            # 6. 流式返回
            async for chunk in llm_stream:
                content_piece = chunk.choices[0].delta.content or ""
                full_response_content += content_piece

                stream_chunk = StreamChunk(
                    conversation_id=request.conversation_id,
                    text_chunk=content_piece,
                    is_final=False,
                    timestamp=datetime.utcnow().isoformat()
                )
                yield f"data: {stream_chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.01)

            # 标记流结束
            final_chunk = StreamChunk(
                conversation_id=request.conversation_id,
                text_chunk="",
                is_final=True,
                timestamp=datetime.utcnow().isoformat()
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            logger.info(f"Request ID: {request_id} - Finished streaming response for conversation: {request.conversation_id}")

        except Exception as e:
            logger.error(f"Request ID: {request_id} - Exception during image chat: {e}")
            error_message = {
                "success": False,
                "error": "ImageChatProcessingError",
                "detail": str(e)
            }
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
            # 7. 保存对话历史
            if full_response_content:
                # Combine original question and image type for history
                user_message = f"[Image Analysis: {request.image_type.value}] {request.question}"
                await self.mongo_service.save_message(request.conversation_id, "user", user_message)
                await self.mongo_service.save_message(request.conversation_id, "assistant", full_response_content)
                logger.info(f"Request ID: {request_id} - Saved conversation history for: {request.conversation_id}")

    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """处理聊天请求"""
        try:
            # 生成对话ID（如果没有提供）
            conversation_id = request.conversation_id or self._generate_conversation_id()

            # 异步获取对话历史
            history_task = self.mongo_service.get_conversation_history(conversation_id)

            # 保存用户消息
            await self.mongo_service.save_message(conversation_id, "user", request.question)

            # 获取历史对话
            history = await history_task

            # 构建对话上下文
            context = self._build_context(history, request.question)

            # 调用LLM服务
            llm_response = await self.llm_service.generate_response(context)

            # 保存助手回复
            await self.mongo_service.save_message(conversation_id, "assistant", llm_response)

            # 缓存最新对话
            await self._cache_conversation(conversation_id)

            return ChatResponse(
                success=True,
                response=llm_response,
                conversation_id=conversation_id
            )

        except Exception as e:
            return ChatResponse(
                success=False,
                error=str(e),
                conversation_id=request.conversation_id
            )

    def _build_context(self, history: list[dict], current_question: str) -> str:
        """构建对话上下文"""
        context_parts = []

        # 添加历史对话
        for msg in history[-5:]:  # 只取最近5条
            role = msg.get("role", "")
            content = msg.get("content", "")
            context_parts.append(f"{role}: {content}")

        # 添加当前问题
        context_parts.append(f"user: {current_question}")

        return "\n".join(context_parts)

    def _generate_conversation_id(self) -> str:
        """生成对话ID"""
        import uuid
        return str(uuid.uuid4())

    async def _cache_conversation(self, conversation_id: str):
        """缓存对话历史"""
        try:
            # 获取最新对话历史
            history = await self.mongo_service.get_conversation_history(conversation_id, limit=20)

            # 转换为缓存格式
            cache_messages = []
            for msg in history:
                cache_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat()
                })

            # 缓存到Redis
            await self.redis_service.cache_conversation_history(
                conversation_id,
                cache_messages,
                max_messages=20,
                expire_seconds=3600
            )
        except Exception as e:
            # 缓存失败不影响主流程
            pass

    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> list[ChatMessage]:
        """获取对话历史"""
        try:
            # 先尝试从缓存获取
            cached_history = await self.redis_service.get_cached_conversation_history(
                conversation_id, limit
            )

            if cached_history:
                return [
                    ChatMessage(
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.fromisoformat(msg["timestamp"]),
                        metadata=msg.get("metadata")
                    )
                    for msg in cached_history
                ]

            # 从数据库获取
            history = await self.mongo_service.get_conversation_history(conversation_id, limit)

            return [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp", datetime.utcnow()),
                    metadata=msg.get("metadata")
                )
                for msg in history
            ]

        except Exception as e:
            return []

    def _rag_retrieval(self, query: str) -> str:
        """模拟RAG知识检索"""
        logger.info(f"Performing RAG retrieval for query: '{query[:50]}...'")
        # In a real application, this would query a vector database.
        return "RAG Knowledge: 狗狗在呕吐黄色泡沫时，通常建议禁食12小时，并观察精神状态。如果持续呕吐或精神萎靡，应立即就医。"

    def _build_prompt(self, question: str, pet_info, history, rag_knowledge: str, image_descriptions: str = None) -> str:
        """构建最终的提示词"""
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

        prompt = f"""你是一个专业的宠物医生。请根据以下信息，用中文回答用户的问题。

[宠物信息]
{json.dumps(pet_info.model_dump(), indent=2, ensure_ascii=False)}

[对话历史]
{history_str}

[相关知识库]
{rag_knowledge}
"""
        if image_descriptions:
            prompt += f"""
[图片分析结果]
{image_descriptions}
"""
        prompt += f"""
[用户当前问题]
{question}

请根据以上所有信息，提供专业、详细的回答。
"""
        logger.info(f"Built prompt: {prompt[:300]}...")
        return prompt
