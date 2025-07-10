# /app/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# 定位项目根目录
# D:\Prj\github\gemini-cli-deployment -> D:\Prj\github\gemini-cli-deployment
# or D:\Prj\github\gemini-cli-deployment\app -> D:\Prj\github\gemini-cli-deployment
# This ensures that the .env file is found correctly regardless of where the script is run from.
# Note: This assumes a standard project structure where `config.py` is in `app/core/`.
# Adjust if your structure is different.
# For example, if running from `D:\Prj\github\gemini-cli-deployment`, Path(__file__).resolve() is `D:\Prj\github\gemini-cli-deployment\app\core\config.py`
# .parent is `D:\Prj\github\gemini-cli-deployment\app\core`
# .parent.parent is `D:\Prj\github\gemini-cli-deployment\app`
# .parent.parent.parent is `D:\Prj\github\gemini-cli-deployment`
env_path = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # --- Project ---
    PROJECT_NAME: str = "Pet Medical Assistant API"
    API_V1_STR: str = "/api/v1"

    # --- JWT ---
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- LLM Service (ds-vet-answer-32B) ---
    LLM_OPENAI_BASE_URL: str = "https://gateway.haoshouyi.com/vet1-scope/v1/"
    LLM_OPENAI_API_KEY: str = "sk-12qsw3wh19pqhouf6fxmuit"
    LLM_MODEL_NAME: str = "ds-vet-answer-32B"

    # --- Multimodal Service (ds-vet-vl-72B) ---
    MULTIMODAL_BASE_URL: str = "https://platformx.vetmew.com:21006"
    MULTIMODAL_API_KEY: str = "vmac8e79f1e084400d"
    MULTIMODAL_API_SECRET: str = "1ghhni82nqzp5jao2umlfnvfium7crqo"

    # --- Pet Info Service ---
    PET_INFO_API_BASE_URL: str = "https://api.pet-info-service.com/v1"
    PET_INFO_API_CLIENT_ID: str = "CLIENT12345"
    PET_INFO_API_SECRET_KEY: str = "a_very_secret_pet_info_key" # Should be in .env

    # --- Database ---
    MONGO_CONNECTION_STRING: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "pet_medical_chat"

    # --- Caching & Rate Limiting ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/pet_api.log"

    class Config:
        # When you run the application, Pydantic will try to read these environment variables.
        # If they are not found, it will use the default values defined above.
        # The `env_file` tells Pydantic to load variables from a .env file.
        env_file = env_path
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> Settings:
    # Create logs directory if it doesn't exist
    log_dir = Path(Settings().LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    return Settings()


settings = get_settings()
