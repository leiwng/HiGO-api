# /app/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# 定位项目根目录
# Project Directory: /backup/wanglei/prj/github/leiwng/HiGO-api; ./HiGO-api
# This ensures that the .env file is found correctly regardless of where the script is run from.
# Note: This assumes a standard project structure where `config.py` is in `./HiGO-api/app/core/`.
# .parent is `./HiGO-api/app/`
# .parent.parent is `./HiGO-api/`
env_path = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # --- Project ---
    PROJECT_NAME: str = "HiGO Pet Medical Chat API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # --- Database ---
    MONGODB_URL: str = "mongodb://localhost:27017/"
    MONGODB_DB_NAME: str = "pet_medical_chat"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20

    # --- Password Policy ---
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True

    # --- Rate Limiting ---
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30

    # --- LLM Service ---
    LLM_API_URL: str = "http://localhost:8001"
    LLM_API_KEY: str = "your-llm-api-key"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7

    # --- HTTP Client ---
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3

    class Config:
        # When you run the application, Pydantic will try to read these environment variables.
        # If they are not found, it will use the default values defined above.
        # The `env_file` tells Pydantic to load variables from a .env file.
        env_file = env_path
        env_file_encoding = 'utf-8'
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    # Create logs directory if it doesn't exist
    log_dir = Path(Settings().LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    return Settings()


settings = get_settings()
