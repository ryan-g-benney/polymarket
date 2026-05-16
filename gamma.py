from api import PolymarketAPI, GAMMA_BASE


class GammaAPI(PolymarketAPI):
    _base_url = GAMMA_BASE

    # --- Status ---

    async def get_status(self) -> dict:
        return await self._get("/")

    # --- Events ---

    async def get_events(
        self,
        limit: int = 20,
        offset: int = None,
        order: str = None,
        ascending: bool = None,
        id: list[int] = None,
        slug: list[str] = None,
        closed: bool = None,
        live: bool = None,
        featured: bool = None,
        title_search: str = None,
        liquidity_min: float = None,
        liquidity_max: float = None,
        volume_min: float = None,
        volume_max: float = None,
        start_date_min: str = None,
        start_date_max: str = None,
        end_date_min: str = None,
        end_date_max: str = None,
        tag_id: list[int] = None,
        tag_slug: str = None,
        series_id: list[int] = None,
    ) -> list:
        return await self._get(
            "/events",
            limit=limit,
            offset=offset,
            order=order,
            ascending=ascending,
            id=id,
            slug=slug,
            closed=closed,
            live=live,
            featured=featured,
            title_search=title_search,
            liquidity_min=liquidity_min,
            liquidity_max=liquidity_max,
            volume_min=volume_min,
            volume_max=volume_max,
            start_date_min=start_date_min,
            start_date_max=start_date_max,
            end_date_min=end_date_min,
            end_date_max=end_date_max,
            tag_id=tag_id,
            tag_slug=tag_slug,
            series_id=series_id,
        )

    async def get_events_keyset(
        self,
        limit: int = 20,
        after_cursor: str = None,
        order: str = None,
        ascending: bool = None,
        closed: bool = None,
        live: bool = None,
        featured: bool = None,
        title_search: str = None,
        liquidity_min: float = None,
        liquidity_max: float = None,
        volume_min: float = None,
        volume_max: float = None,
        tag_id: list[int] = None,
        tag_slug: str = None,
        series_id: list[int] = None,
    ) -> dict:
        return await self._get(
            "/events/keyset",
            limit=limit,
            after_cursor=after_cursor,
            order=order,
            ascending=ascending,
            closed=closed,
            live=live,
            featured=featured,
            title_search=title_search,
            liquidity_min=liquidity_min,
            liquidity_max=liquidity_max,
            volume_min=volume_min,
            volume_max=volume_max,
            tag_id=tag_id,
            tag_slug=tag_slug,
            series_id=series_id,
        )

    async def get_event(self, id: int) -> dict:
        return await self._get(f"/events/{id}")

    async def get_event_by_slug(self, slug: str) -> dict:
        return await self._get(f"/events/slug/{slug}")

    async def get_event_tags(self, id: int) -> list:
        return await self._get(f"/events/{id}/tags")

    # --- Markets ---

    async def get_markets(
        self,
        limit: int = 20,
        offset: int = None,
        order: str = None,
        ascending: bool = None,
        id: list[int] = None,
        slug: list[str] = None,
        closed: bool = None,
        clob_token_ids: list[str] = None,
        condition_ids: list[str] = None,
        liquidity_num_min: float = None,
        liquidity_num_max: float = None,
        volume_num_min: float = None,
        volume_num_max: float = None,
        start_date_min: str = None,
        start_date_max: str = None,
        end_date_min: str = None,
        end_date_max: str = None,
        tag_id: list[int] = None,
    ) -> list:
        return await self._get(
            "/markets",
            limit=limit,
            offset=offset,
            order=order,
            ascending=ascending,
            id=id,
            slug=slug,
            closed=closed,
            clob_token_ids=clob_token_ids,
            condition_ids=condition_ids,
            liquidity_num_min=liquidity_num_min,
            liquidity_num_max=liquidity_num_max,
            volume_num_min=volume_num_min,
            volume_num_max=volume_num_max,
            start_date_min=start_date_min,
            start_date_max=start_date_max,
            end_date_min=end_date_min,
            end_date_max=end_date_max,
            tag_id=tag_id,
        )

    async def get_markets_keyset(
        self,
        limit: int = 20,
        after_cursor: str = None,
        order: str = None,
        ascending: bool = None,
        closed: bool = None,
        clob_token_ids: list[str] = None,
        condition_ids: list[str] = None,
        liquidity_num_min: float = None,
        liquidity_num_max: float = None,
        volume_num_min: float = None,
        volume_num_max: float = None,
        tag_id: list[int] = None,
    ) -> dict:
        return await self._get(
            "/markets/keyset",
            limit=limit,
            after_cursor=after_cursor,
            order=order,
            ascending=ascending,
            closed=closed,
            clob_token_ids=clob_token_ids,
            condition_ids=condition_ids,
            liquidity_num_min=liquidity_num_min,
            liquidity_num_max=liquidity_num_max,
            volume_num_min=volume_num_min,
            volume_num_max=volume_num_max,
            tag_id=tag_id,
        )

    async def get_market(self, id: int) -> dict:
        return await self._get(f"/markets/{id}")

    async def get_market_by_slug(self, slug: str) -> dict:
        return await self._get(f"/markets/slug/{slug}")

    async def get_market_tags(self, id: int) -> list:
        return await self._get(f"/markets/{id}/tags")

    # --- Tags ---

    async def get_tags(
        self,
        limit: int = 20,
        offset: int = None,
        order: str = None,
        ascending: bool = None,
        is_carousel: bool = None,
    ) -> list:
        return await self._get(
            "/tags",
            limit=limit,
            offset=offset,
            order=order,
            ascending=ascending,
            is_carousel=is_carousel,
        )
