from api import PolymarketAPI, CLOB_BASE


class ClobAPI(PolymarketAPI):
    _base_url = CLOB_BASE

    # --- Server ---

    async def get_server_time(self) -> int:
        return await self._get("/time")

    # --- Order Book ---

    async def get_order_book(self, token_id: str) -> dict:
        return await self._get("/book", token_id=token_id)

    async def get_order_books(self, token_ids: list[str]) -> list:
        return await self._post("/books", json=[{"token_id": t} for t in token_ids])

    # --- Midpoints ---

    async def get_midpoint(self, token_id: str) -> dict:
        return await self._get("/midpoint", token_id=token_id)

    async def get_midpoints(self, token_ids: list[str]) -> dict:
        return await self._get("/midpoints", token_id=token_ids)

    async def get_midpoints_bulk(self, token_ids: list[str]) -> dict:
        return await self._post("/midpoints", json=[{"token_id": t} for t in token_ids])

    # --- Prices ---

    async def get_price(self, token_id: str, side: str) -> dict:
        return await self._get("/price", token_id=token_id, side=side)

    async def get_prices(self, token_ids: list[str], sides: list[str]) -> dict:
        return await self._get("/prices", token_id=token_ids, side=sides)

    async def get_prices_bulk(self, requests: list[dict]) -> dict:
        """requests: list of {"token_id": str, "side": str}"""
        return await self._post("/prices", json=requests)

    # --- Spreads ---

    async def get_spread(self, token_id: str) -> dict:
        return await self._get("/spread", token_id=token_id)

    async def get_spreads_bulk(self, token_ids: list[str]) -> dict:
        return await self._post("/spreads", json=[{"token_id": t} for t in token_ids])

    # --- Last Trade Prices ---

    async def get_last_trade_price(self, token_id: str) -> dict:
        return await self._get("/last-trade-price", token_id=token_id)

    async def get_last_trade_prices(self, token_ids: list[str]) -> dict:
        return await self._get("/last-trades-prices", token_id=token_ids)

    async def get_last_trade_prices_bulk(self, token_ids: list[str]) -> dict:
        return await self._post("/last-trades-prices", json=[{"token_id": t} for t in token_ids])

    # --- Market Info ---

    async def get_tick_size(self, token_id: str) -> dict:
        return await self._get(f"/tick-size/{token_id}")

    async def get_fee_rate(self, token_id: str) -> dict:
        return await self._get(f"/fee-rate/{token_id}")

    async def get_clob_market(self, condition_id: str) -> dict:
        return await self._get(f"/clob-markets/{condition_id}")

    async def get_market_by_token(self, token_id: str) -> dict:
        return await self._get(f"/markets-by-token/{token_id}")

    # --- Price History ---

    async def get_prices_history(
        self,
        token_id: str,
        start_ts: int = None,
        end_ts: int = None,
        interval: str = None,
        fidelity: int = None,
    ) -> dict:
        return await self._get(
            "/prices-history",
            market=token_id,
            startTs=start_ts,
            endTs=end_ts,
            interval=interval,
            fidelity=fidelity,
        )

    async def get_prices_history_bulk(self, requests: list[dict]) -> list:
        """requests: list of {"market": str, "startTs": int, "endTs": int, ...}"""
        return await self._post("/batch-prices-history", json=requests)
