import asyncio
import httpx

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
DATA_BASE = "https://data-api.polymarket.com"


class PolymarketAPI:
    _base_url: str = ""
    _client: httpx.AsyncClient | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._client = None
        cls._lock = asyncio.Lock()

    async def __aenter__(self):
        cls = type(self)
        async with cls._lock:
            if cls._client is None:
                cls._client = httpx.AsyncClient(base_url=cls._base_url, timeout=30.0)
        return self

    async def __aexit__(self, *args):
        pass  # client is shared — call cls.aclose() to shut it down

    @classmethod
    async def aclose(cls):
        async with cls._lock:
            if cls._client is not None:
                await cls._client.aclose()
                cls._client = None

    async def _get(self, path: str, **params) -> dict | list:
        cls = type(self)
        if cls._client is None:
            raise RuntimeError(f"{cls.__name__} not initialized — use 'async with'")
        filtered = {k: v for k, v in params.items() if v is not None}
        resp = await cls._client.get(path, params=filtered)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json=None) -> dict | list:
        cls = type(self)
        if cls._client is None:
            raise RuntimeError(f"{cls.__name__} not initialized — use 'async with'")
        resp = await cls._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()
