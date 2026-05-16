# Polymarket API

Python client for the Polymarket public APIs using `httpx`.

## APIs

| API | Base URL | Auth Required |
|-----|----------|---------------|
| Gamma | `https://gamma-api.polymarket.com` | No |
| CLOB | `https://clob.polymarket.com` | Public endpoints: No / Trading: Yes |
| Data | `https://data-api.polymarket.com` | No |

---

## Gamma API (`gamma.py`)

Market metadata, events, tags, series, and search.

### Events

| Method | Path | Description |
|--------|------|-------------|
| GET | `/events` | List events (offset pagination) |
| GET | `/events/keyset` | List events (cursor pagination, max 500) |
| GET | `/events/{id}` | Get event by ID |
| GET | `/events/slug/{slug}` | Get event by slug |
| GET | `/events/{id}/tags` | Get tags for an event |

**Common query params for `/events` and `/events/keyset`:**
- `limit` (int, max 500)
- `order` (string, comma-separated field names)
- `ascending` (bool)
- `after_cursor` (string, keyset only)
- `offset` (int, offset pagination only)
- `id` (int[])
- `slug` (string[])
- `closed` (bool)
- `live` (bool)
- `featured` (bool)
- `title_search` (string)
- `liquidity_min` / `liquidity_max` (number)
- `volume_min` / `volume_max` (number)
- `start_date_min` / `start_date_max` (datetime)
- `end_date_min` / `end_date_max` (datetime)
- `tag_id` (int[])
- `tag_slug` (string)
- `series_id` (int[])

### Markets

| Method | Path | Description |
|--------|------|-------------|
| GET | `/markets` | List markets (offset pagination) |
| GET | `/markets/keyset` | List markets (cursor pagination, max 100) |
| GET | `/markets/{id}` | Get market by ID |
| GET | `/markets/slug/{slug}` | Get market by slug |
| GET | `/markets/{id}/tags` | Get tags for a market |

**Common query params for `/markets` and `/markets/keyset`:**
- `limit` (int, max 100)
- `order` / `ascending` / `after_cursor` / `offset`
- `id` (int[])
- `slug` (string[])
- `closed` (bool)
- `clob_token_ids` (string[])
- `condition_ids` (string[])
- `liquidity_num_min` / `liquidity_num_max` (number)
- `volume_num_min` / `volume_num_max` (number)
- `start_date_min` / `start_date_max` (datetime)
- `end_date_min` / `end_date_max` (datetime)
- `tag_id` (int[])

### Tags

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tags` | List all tags |

**Params:** `limit`, `offset`, `order`, `ascending`, `is_carousel`

### Status

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API health / status |

---

## CLOB API (`clob.py`) — Public endpoints only

Order book data, pricing, and market info. Trading endpoints (order placement/cancellation) require L2 auth and are **not implemented** here.

### Pricing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/midpoint` | Midpoint price for a token (`token_id`) |
| GET | `/midpoints` | Midpoints for multiple tokens (`token_id[]`) |
| POST | `/midpoints` | Midpoints via request body |
| GET | `/price` | Best market price (`token_id`, `side`) |
| GET | `/prices` | Multiple prices (`token_id[]`, `side[]`) |
| POST | `/prices` | Multiple prices via request body |
| GET | `/spread` | Bid-ask spread (`token_id`) |
| POST | `/spreads` | Spreads for multiple tokens |
| GET | `/last-trade-price` | Last trade price (`token_id`) |
| GET | `/last-trades-prices` | Last prices for multiple tokens (`token_id[]`) |
| POST | `/last-trades-prices` | Last prices via request body |

### Order Book

| Method | Path | Description |
|--------|------|-------------|
| GET | `/book` | Order book for a token (`token_id`) |
| POST | `/books` | Order books for multiple tokens |

### Market Info

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tick-size/{token_id}` | Minimum price increment for a token |
| GET | `/fee-rate/{token_id}` | Base fee rate for a token |
| GET | `/clob-markets/{condition_id}` | All CLOB parameters for a market |
| GET | `/markets-by-token/{token_id}` | Parent market for a token |
| GET | `/prices-history` | Historical prices (`market`, `startTs`, `endTs`, `interval`, `fidelity`) |
| POST | `/batch-prices-history` | Historical prices for multiple markets |

### Server

| Method | Path | Description |
|--------|------|-------------|
| GET | `/time` | Current server Unix timestamp |

---

## Data API (`data.py`)

Analytics, positions, and market holder data.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/oi` | Open interest (`market_id` or `token_id`) |
| GET | `/live-volume` | Live trading volume for an event (`event_id`) |
| GET | `/holders` | Top holders for markets (`market_id[]`) |

---

## Usage

```python
from gamma import GammaAPI
from clob import ClobAPI
from data import DataAPI

# Gamma — events and markets
with GammaAPI() as gamma:
    events = gamma.get_events(limit=10, live=True)
    market = gamma.get_market_by_slug("will-trump-win-2024")

# CLOB — pricing and order book
with ClobAPI() as clob:
    book = clob.get_order_book("some-token-id")
    mid = clob.get_midpoint("some-token-id")
    history = clob.get_prices_history("some-token-id", interval="1h")

# Data — analytics
with DataAPI() as data:
    oi = data.get_open_interest(market_id="some-market-id")
```
# polymarket
# polymarket
