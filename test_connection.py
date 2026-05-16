"""
Integration tests — real HTTP calls, no mocking. Requires network access.

Run with: pytest test_connection.py -v
"""

import json
import pytest
from gamma import GammaAPI
from clob import ClobAPI
from data import DataAPI


@pytest.fixture(scope="module")
async def token_id() -> str | None:
    """Fetch one active CLOB token ID from Gamma to reuse across CLOB tests."""
    async with GammaAPI() as gamma:
        markets = await gamma.get_markets(limit=10, closed=False)
    for m in markets:
        tokens = m.get("clobTokenIds") or []
        if isinstance(tokens, str):
            try:
                tokens = json.loads(tokens)
            except Exception:
                tokens = [tokens]
        if tokens:
            return tokens[0]
    return None


# ---------------------------------------------------------------------------
# Gamma API
# ---------------------------------------------------------------------------

class TestGammaAPI:
    async def test_get_events_returns_list(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_events(limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    async def test_get_events_live_filter(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_events(limit=3, live=True)
        assert isinstance(result, list)

    async def test_get_events_keyset_returns_cursor(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_events_keyset(limit=5)
        assert isinstance(result, dict)
        assert "events" in result

    async def test_get_events_keyset_pagination(self):
        async with GammaAPI() as gamma:
            page1 = await gamma.get_events_keyset(limit=2)
            cursor = page1.get("next_cursor")
            if cursor:
                page2 = await gamma.get_events_keyset(limit=2, after_cursor=cursor)
                assert "events" in page2
                ids1 = {e["id"] for e in page1["events"]}
                ids2 = {e["id"] for e in page2["events"]}
                assert ids1.isdisjoint(ids2), "Cursor pagination returned duplicate events"

    async def test_get_event_by_id(self):
        async with GammaAPI() as gamma:
            events = await gamma.get_events(limit=1)
            assert events
            event = await gamma.get_event(events[0]["id"])
        assert isinstance(event, dict)
        assert event["id"] == events[0]["id"]

    async def test_get_event_by_slug(self):
        async with GammaAPI() as gamma:
            events = await gamma.get_events(limit=1)
            assert events
            slug = events[0].get("slug")
            if slug:
                event = await gamma.get_event_by_slug(slug)
                assert event.get("slug") == slug

    async def test_get_markets_returns_list(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_markets(limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5

    async def test_get_markets_keyset_returns_cursor(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_markets_keyset(limit=5)
        assert isinstance(result, dict)
        assert "markets" in result

    async def test_get_market_by_id(self):
        async with GammaAPI() as gamma:
            markets = await gamma.get_markets(limit=1)
            assert markets
            market = await gamma.get_market(markets[0]["id"])
        assert isinstance(market, dict)
        assert market["id"] == markets[0]["id"]

    async def test_get_market_by_slug(self):
        async with GammaAPI() as gamma:
            markets = await gamma.get_markets(limit=1)
            assert markets
            slug = markets[0].get("slug")
            if slug:
                market = await gamma.get_market_by_slug(slug)
                assert isinstance(market, dict)

    async def test_get_tags_returns_list(self):
        async with GammaAPI() as gamma:
            result = await gamma.get_tags(limit=10)
        assert isinstance(result, list)
        assert len(result) <= 10

    async def test_get_tags_have_expected_fields(self):
        async with GammaAPI() as gamma:
            tags = await gamma.get_tags(limit=5)
        assert tags
        assert "id" in tags[0] or "slug" in tags[0]

    async def test_singleton_client_not_reopened(self):
        async with GammaAPI() as g1:
            client1 = GammaAPI._client
        async with GammaAPI() as g2:
            client2 = GammaAPI._client
        assert client1 is client2, "A second AsyncClient was created — singleton broken"


# ---------------------------------------------------------------------------
# CLOB API
# ---------------------------------------------------------------------------

class TestClobAPI:
    async def test_get_server_time(self):
        async with ClobAPI() as clob:
            result = await clob.get_server_time()
        assert isinstance(result, int)
        assert result > 0

    async def test_get_order_book(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_order_book(token_id)
        assert isinstance(result, dict)

    async def test_get_midpoint(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_midpoint(token_id)
        assert isinstance(result, dict)

    async def test_get_spread(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_spread(token_id)
        assert isinstance(result, dict)

    async def test_get_last_trade_price(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_last_trade_price(token_id)
        assert isinstance(result, dict)

    async def test_get_price_buy(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_price(token_id, side="buy")
        assert isinstance(result, dict)

    async def test_get_tick_size(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_tick_size(token_id)
        assert isinstance(result, dict)

    async def test_get_fee_rate(self, token_id):
        if not token_id:
            pytest.skip("No token_id available")
        async with ClobAPI() as clob:
            result = await clob.get_fee_rate(token_id)
        assert isinstance(result, dict)

    async def test_singleton_client_not_reopened(self):
        async with ClobAPI() as c1:
            client1 = ClobAPI._client
        async with ClobAPI() as c2:
            client2 = ClobAPI._client
        assert client1 is client2, "A second AsyncClient was created — singleton broken"


# ---------------------------------------------------------------------------
# Data API
# ---------------------------------------------------------------------------

class TestDataAPI:
    async def test_get_open_interest_no_filter(self):
        async with DataAPI() as data:
            result = await data.get_open_interest()
        assert result is not None

    async def test_get_live_volume(self):
        async with GammaAPI() as gamma:
            events = await gamma.get_events(limit=5, live=True)
        if not events:
            pytest.skip("No live events available")
        async with DataAPI() as data:
            result = await data.get_live_volume(events[0]["id"])
        assert isinstance(result, list)

    async def test_get_holders(self):
        async with GammaAPI() as gamma:
            markets = await gamma.get_markets(limit=5)
        condition_id = next((m["conditionId"] for m in markets if m.get("conditionId")), None)
        if not condition_id:
            pytest.skip("No condition_id available")
        async with DataAPI() as data:
            result = await data.get_holders(condition_id)
        assert isinstance(result, list)
