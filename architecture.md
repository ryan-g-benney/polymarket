# Architecture — Polymarket Trading Harness

> System architecture, data flows, and component reference.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     Polymarket Public APIs                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Gamma API   │  │   CLOB API   │  │   Data API   │       │
│  │  (metadata)   │  │   (prices)   │  │  (analytics) │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    API Client Layer (Python)                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  PolymarketAPI (api.py) — Singleton AsyncClient      │    │
│  │  ├── _get(endpoint, params) → dict                   │    │
│  │  └── _post(endpoint, data) → dict                    │    │
│  └──────────────────────────────────────────────────────┘    │
│      ▲              ▲              ▲                         │
│  ┌───┴────┐    ┌────┴───┐    ┌────┴───┐                     │
│  │GammaAPI│    │ClobAPI │    │DataAPI │                     │
│  │gamma.py│    │clob.py │    │data.py │                     │
│  └────────┘    └────────┘    └────────┘                     │
└──────────────────────────────────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                  Data Collection Layer                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  backtest.py                                          │    │
│  │  ├── collect_markets() — discover top-volume markets  │    │
│  │  ├── fetch_market() — aggregate per-market data       │    │
│  │  └── Output → EDA/<slug>/{price_history,trades}.csv   │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│                  Analysis Layer (Notebooks)                    │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────┐       │
│  │ eda.ipynb  │ │bet_positions │ │  bet_timeline    │       │
│  │            │ │  .ipynb      │ │     .ipynb       │       │
│  └────────────┘ └──────────────┘ └──────────────────┘       │
│  ┌────────────────────┐ ┌────────────────────────┐          │
│  │ market_analysis    │ │   maduro_bets          │          │
│  │       .ipynb       │ │       .ipynb           │          │
│  └────────────────────┘ └────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│              Future: Backtesting & Trading Engine              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Strategy │  │ Backtest │  │  Risk    │  │  Order   │    │
│  │ Engine   │  │  Runner  │  │ Manager  │  │ Executor │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. API Client Architecture

### 2.1 Base Class: `PolymarketAPI` (`api.py`)

The foundation of all API interactions. Manages a **singleton** `httpx.AsyncClient` instance for connection pooling and clean lifecycle management.

```python
class PolymarketAPI:
    _client: httpx.AsyncClient | None = None   # Shared singleton

    async def __aenter__(self):
        if self._client is None:
            self.__class__._client = httpx.AsyncClient(...)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self.__class__._client = None

    async def _get(self, endpoint, params=None) -> dict: ...
    async def _post(self, endpoint, data=None) -> dict: ...
```

**Key Design Decisions:**
- Singleton pattern ensures connection reuse across all API client instances.
- `async with` context manager guarantees cleanup.
- All subclasses inherit `_get` and `_post` — they never create their own HTTP clients.

### 2.2 Gamma API (`gamma.py`)

**Base URL:** `https://gamma-api.polymarket.com`

| Method | Purpose | Key Parameters |
|---|---|---|
| `get_markets()` | Search/list markets | `tag_slug`, `active`, `limit`, `offset` |
| `get_market(slug)` | Single market by slug | `slug` |
| `get_events()` | List events (groups of markets) | `slug`, `limit`, `offset` |
| `get_event(slug)` | Single event by slug | `slug` |
| `get_tags()` | Available tag categories | — |
| `get_series()` | Market series | `slug` |

**Notes:**
- Primary source for market discovery and metadata.
- Markets are identified by `slug` (human-readable) and `condition_id` (on-chain identifier).
- Supports pagination via `limit`/`offset`.

### 2.3 CLOB API (`clob.py`)

**Base URL:** `https://clob.polymarket.com`

| Method | Purpose | Key Parameters |
|---|---|---|
| `get_order_book(token_id)` | Live order book | `token_id` |
| `get_midpoint(token_id)` | Current mid price | `token_id` |
| `get_spread(token_id)` | Bid-ask spread | `token_id` |
| `get_price_history(token_id)` | Historical OHLCV candles | `token_id`, `interval`, `fidelity` |

**Notes:**
- `token_id` identifies a specific outcome token (YES or NO side of a market).
- Price history provides daily candles — the primary source for backtesting time series.
- **No trading endpoints implemented** — this is read-only for now.

### 2.4 Data API (`data.py`)

**Base URL:** `https://data-api.polymarket.com`

| Method | Purpose | Key Parameters |
|---|---|---|
| `get_trades(condition_id)` | Individual trade fills | `market`, `limit`, `offset` |
| `get_volume(condition_id)` | Trading volume | `market` |
| `get_holders(condition_id)` | Position holders | `market` |
| `get_open_interest(condition_id)` | Open interest | `market` |

**Notes:**
- Paginated — max 500 per page, ≈3,000 total (hard API cap).
- Trade fills provide individual bet-level data: timestamp, price, size, side, outcome.
- For high-volume markets, the 3,000-fill window compresses near resolution.

---

## 3. Data Collection Pipeline

### 3.1 `backtest.py` Flow

```
1. collect_markets()
   ├── Search across political query strings via GammaAPI
   ├── Filter by volume (top-20)
   └── Return deduplicated market list

2. For each market → fetch_market(market)
   ├── Fetch metadata (GammaAPI)
   ├── Fetch YES token price history (ClobAPI)
   ├── Fetch NO token price history (ClobAPI)
   ├── Fetch trade fills (DataAPI, paginated)
   └── Write to EDA/<slug>/
       ├── price_history.csv
       └── trades.csv

3. Write EDA/markets.csv (master catalogue)
```

### 3.2 Data Schemas

**`markets.csv`** — Master catalogue

| Column | Type | Description |
|---|---|---|
| `slug` | str | Market slug identifier |
| `question` | str | Market question text |
| `condition_id` | str | On-chain condition ID |
| `volume` | float | Total volume traded |
| `active` | bool | Whether market is still open |
| `resolution` | str | Outcome (if resolved) |

**`price_history.csv`** — Per-market candle data

| Column | Type | Description |
|---|---|---|
| `timestamp` | int64 | Unix seconds |
| `price` | float64 | Daily close price (0-1 probability) |

**`trades.csv`** — Per-market fill data

| Column | Type | Description |
|---|---|---|
| `timestamp` | int64 | Unix seconds |
| `price` | float64 | Execution price |
| `size` | float64 | USDC value |
| `side` | str | BUY or SELL |
| `outcome` | str | YES or NO |

> ⚠️ **Timestamp Note:** API returns Unix seconds. Notebooks multiply by 1,000,000 and cast to `pl.Datetime('us')` for Polars compatibility.

---

## 4. EDA Notebook Catalogue

### 4.1 `eda.ipynb` — Market Volume & Resolution Analysis
- **Purpose:** Initial overview of the top-20 political markets.
- **Data:** `markets.csv`, per-market `price_history.csv`.
- **Key Outputs:** Volume distribution, resolution outcomes, price candle normalization.

### 4.2 `bet_positions.ipynb` — Bet Direction & Flow Analysis
- **Purpose:** Track BUY/SELL events over time; visualize net market sentiment vs price.
- **Data:** Per-market `trades.csv`, `price_history.csv`.
- **Key Outputs:** Cumulative money flow charts, bet direction breakdowns.

### 4.3 `bet_timeline.ipynb` — Individual Bet Timeline
- **Purpose:** Plot every individual bet (size vs time, BUY/SELL colored) with price overlay.
- **Data:** Live API fetch (≈3,000 fills per market) + local `price_history.csv`.
- **Key Outputs:** Two panels per market — (1) scatter of all fills, (2) cumulative BUY/SELL USDC flow.
- **Note:** Fetches live trade data at runtime — takes ≈3 seconds per market.

### 4.4 `market_analysis.ipynb` — Money Influx & Insider Signal Detection
- **Purpose:** Measure money entering each market per unit time; detect potential insider trading.
- **Key Innovation:** Qualitative **insider score** (0-10) based on:
  - BUY dominance ratio (>80% → +4 points)
  - Whale concentration (max bet / median bet ratio)
  - Time spread (sustained accumulation over many days)
- **Data:** Local `markets.csv`, per-market `trades.csv`.
- **Key Outputs:** Per-market bar charts with insider signal scores.

### 4.5 `maduro_bets.ipynb` — Van Dyke Case Forensic Analysis
- **Purpose:** Analyse bet-level data across 8 Maduro capture/removal markets to surface patterns consistent with informed trading.
- **Background:** U.S. Army Special Forces Master Sgt. Gannon Van Dyke was charged with using classified information to place bets on Polymarket.
- **Data:** Live API fetch for 8 specific Maduro-related markets (hardcoded `condition_id` values).
- **Key Outputs:** Per-market charts showing bet timing, size, and direction relative to price movements.

---

## 5. Testing Architecture

```
test_connection.py
├── Gamma API connectivity tests
│   ├── Test market search
│   ├── Test single market fetch
│   └── Test event/tag/series endpoints
├── CLOB API connectivity tests
│   ├── Test order book
│   ├── Test midpoint/spread
│   └── Test price history
├── Data API connectivity tests
│   ├── Test trade fetch
│   └── Test volume/holders
└── Client lifecycle tests
    └── Verify singleton pattern / cleanup

conftest.py
└── Fixture: graceful AsyncClient teardown

pytest.ini
└── asyncio_mode = auto
```

**Limitations:**
- All tests require live network access (integration-only).
- No mocked responses — tests are non-deterministic.
- Future: Add `pytest-httpx` for response mocking.

---

## 6. Future Architecture Targets

### 6.1 Database Layer (Phase 2)
```
SQLite / DuckDB
├── markets (metadata)
├── candles (price history)
├── fills (individual trades)
└── signals (computed indicators)
```

### 6.2 Strategy Engine (Phase 3)
```python
class Strategy(ABC):
    @abstractmethod
    async def on_candle(self, market_id, candle): ...

    @abstractmethod
    async def on_trade(self, market_id, trade): ...

    @abstractmethod
    def get_signal(self) -> Signal: ...
```

### 6.3 Execution Layer (Phase 5)
```
Order Executor
├── Place order (CLOB API POST)
├── Cancel order
├── Amend order
├── Position tracker
└── P&L calculator
```

---

## 7. Dependency Graph

```
httpx ──────────► api.py ◄──── conftest.py
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    gamma.py    clob.py     data.py
        │           │           │
        └───────────┼───────────┘
                    ▼
              backtest.py
                    │
                    ▼
            EDA/ (notebooks)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    polars     matplotlib   httpx (direct,
                            in some notebooks)
```

> **Note:** Some notebooks (e.g. `bet_timeline.ipynb`, `maduro_bets.ipynb`) fetch data directly from APIs at runtime rather than reading from the collected dataset. This is a design choice for freshness but reduces reproducibility.

---

## 8. Configuration

| Source | Purpose |
|---|---|
| `.env` | API keys, secrets (not committed) |
| `pytest.ini` | Test runner config (`asyncio_mode = auto`) |
| `README.md` | Usage documentation |

**No formal config file** exists for the application layer yet. API base URLs are currently hardcoded in the client modules. Future: Extract to a `config.py` or YAML file.
