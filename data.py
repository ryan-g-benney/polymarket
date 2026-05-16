from api import PolymarketAPI, DATA_BASE


class DataAPI(PolymarketAPI):
    _base_url = DATA_BASE

    async def get_open_interest(
        self,
        market_id: str = None,
        token_id: str = None,
    ) -> dict | list:
        return await self._get("/oi", market_id=market_id, token_id=token_id)

    async def get_live_volume(self, event_id: int | str) -> list:
        return await self._get("/live-volume", id=event_id)

    async def get_holders(self, condition_id: str) -> list:
        """condition_id: the 0x condition ID from Gamma market data."""
        return await self._get("/holders", market=condition_id)

    async def get_trades(self, condition_id: str, limit: int = 500, offset: int = 0) -> list:
        return await self._get("/trades", market=condition_id, limit=limit, offset=offset)
