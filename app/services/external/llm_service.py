# /app/services/external/llm_service.py
from openai import AsyncOpenAI
from fastapi import Depends
from app.core.config import Settings, get_settings

class LLMService:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_OPENAI_API_KEY,
            base_url=settings.LLM_OPENAI_BASE_URL,
        )
        self.model_name = settings.LLM_MODEL_NAME

    async def stream_chat(self, prompt: str):
        """
        Calls the text generation model and streams the response.
        """
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            # Add other parameters like temperature, max_tokens if needed
        )
        async for chunk in stream:
            yield chunk
