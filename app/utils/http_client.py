# /app/utils/http_client.py
import httpx
from contextlib import asynccontextmanager

class AsyncHttpClient:
    """
    A wrapper around httpx.AsyncClient to be used as a dependency.
    This allows us to manage the client's lifecycle properly.
    """
    def __init__(self):
        self._client = httpx.AsyncClient()

    async def get(self, *args, **kwargs):
        return await self._client.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self._client.post(*args, **kwargs)

    async def close(self):
        await self._client.aclose()

# This context manager will be used in the main application's lifespan
@asynccontextmanager
async def lifespan_http_client(app):
    """
    A lifespan context manager for the HTTP client.
    It creates the client on startup and closes it on shutdown.
    """
    client = AsyncHttpClient()
    yield {"http_client": client}
    await client.close()

# A simple dependency to get the client instance
# This is a placeholder and will be replaced by a more robust solution
# in the main.py file using the lifespan event handler.
_http_client_instance = None

def get_http_client_instance():
    global _http_client_instance
    if _http_client_instance is None:
        _http_client_instance = AsyncHttpClient()
    return _http_client_instance
