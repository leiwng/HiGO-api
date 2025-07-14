# /app/core/config.py
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
    # --- App Info ---
    PROJECT_NAME: str = "Pet Medical API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # --- JWT Security ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # 为了兼容性，也支持这些字段名
    SECRET_KEY: str | None = None
    ALGORITHM: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = None

    # --- Database ---
    MONGODB_URL: str
    MONGODB_DB_NAME: str

    # --- Redis ---
    REDIS_URL: str
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
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600

    # --- LLM Service ---
    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    LLM_MODEL: str = "ds-vet-answer-32B"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7

    # --- Multimodal Service ---
    MULTIMODAL_BASE_URL: str
    MULTIMODAL_API_KEY: str
    MULTIMODAL_API_SECRET: str
    MULTIMODAL_TIMEOUT: int = 30

    # --- Pet Info Service ---
    PET_INFO_BASE_URL: str
    PET_INFO_CLIENT_ID: str
    PET_INFO_CLIENT_SECRET: str

    # --- HTTP Client ---
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3

    # --- File Paths ---
    BREED_MAP_FILE: str = "data/pet_breed_0dd7f7.json"

    @property
    def SECRET_KEY_COMPUTED(self) -> str:
        """兼容性属性：返回JWT_SECRET_KEY"""
        return self.SECRET_KEY or self.JWT_SECRET_KEY

    @property
    def ALGORITHM_COMPUTED(self) -> str:
        """兼容性属性：返回JWT_ALGORITHM"""
        return self.ALGORITHM or self.JWT_ALGORITHM

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES_COMPUTED(self) -> int:
        """兼容性属性：返回JWT_EXPIRE_MINUTES"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES or self.JWT_EXPIRE_MINUTES

    class Config:
        # When you run the application, Pydantic will try to read these environment variables.
        # If they are not found, it will use the default values defined above.
        # The `env_file` tells Pydantic to load variables from a .env file.
        env_file = env_path
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # 允许额外的字段
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    # Create logs directory if it doesn't exist
    log_dir = Path(Settings().LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    return Settings()


settings = get_settings()
