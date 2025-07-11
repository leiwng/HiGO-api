# /app/main.py
import time
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from loguru import logger

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.utils.http_client import AsyncHttpClient
from app.services.storage.redis_service import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Setup logging
    setup_logging()
    logger.info("Starting application...")

    # Initialize Redis service first
    try:
        await init_redis()
        logger.info("Redis service initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Redis service: {e}")
        raise

    # Setup Redis for rate limiting
    try:
        redis_connection = redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )
        await FastAPILimiter.init(redis_connection)
        logger.info("Successfully connected to Redis and initialized FastAPILimiter.")
    except Exception as e:
        logger.error(f"Could not connect to Redis or initialize FastAPILimiter: {e}")
        # 如果 Redis 是必需的，您可能希望在此处退出应用程序
        # 现在我们只记录错误
        raise

    # Setup shared HTTP client
    app.state.http_client = AsyncHttpClient()
    logger.info("Async HTTP client created.")

    yield

    # --- Shutdown ---
    logger.info("Shutting down application...")

    # Close HTTP client
    await app.state.http_client.close()
    logger.info("Async HTTP client closed.")

    # Close Redis service
    try:
        await close_redis()
        logger.info("Redis service closed successfully.")
    except Exception as e:
        logger.error(f"Error closing Redis service: {e}")

    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# --- Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming requests and their processing time.
    """
    request_id = f"{request.client.host}:{request.client.port}-{time.time_ns()}"
    logger.info(f"rid={request_id} start request path={request.url.path} method={request.method}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f'{process_time:.2f}'
    logger.info(f"rid={request_id} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for Pydantic's validation errors.
    """
    logger.error(f"Validation error for request {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "ValidationError",
            "detail": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global handler for any unhandled exceptions.
    """
    logger.exception(f"Unhandled exception for request {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "InternalServerError",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )

# --- Dependency Overrides for HTTP Client ---
# This makes the shared httpx client available to dependencies
async def get_http_client(request: Request) -> AsyncHttpClient:
    return request.app.state.http_client

from app.utils import http_client as http_client_module
http_client_module.AsyncHttpClient = get_http_client

# --- API Router ---
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

