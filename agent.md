# Agent — Polymarket Trading Harness

> Behavioural guardrails, conventions, and operating principles for anyone (human or AI) working on this project.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Name** | Polymarket Trading Harness |
| **Purpose** | Data collection, exploratory analysis, backtesting, and (future) automated trading on Polymarket prediction markets |
| **Stage** | Pre-alpha — data collection + EDA established; backtesting & strategy engines not yet built |
| **Primary Language** | Python 3.11+ |
| **Runtime** | Local development; no cloud deployment yet |

---

## 2. Core Principles

1. **Data integrity first** — Every pipeline stage must be auditable. Raw API responses should be preserved alongside any transformed datasets.
2. **Async-native** — All network I/O uses `httpx.AsyncClient` via `async with` context managers. Never use synchronous HTTP in production paths.
3. **Singleton clients** — The `PolymarketAPI` base class manages a shared `AsyncClient` instance. Do not create additional client instances.
4. **Defensive API access** — Polymarket APIs are public but rate-limited. Always implement exponential backoff, pagination guards, and graceful error handling.
5. **Reproducibility** — EDA notebooks must be runnable end-to-end from a clean state. Pin library versions. Commit collected datasets alongside analysis.
6. **No trading endpoints (yet)** — The CLOB API trading endpoints are **not** implemented. The project is strictly read-only against Polymarket for now.

---

## 3. Repository Conventions

### 3.1 Directory Layout

```
polymarket/
├── api.py              # Base PolymarketAPI class (singleton AsyncClient)
├── gamma.py            # Gamma API client (markets, events, tags, series)
├── clob.py             # CLOB API client (order books, prices, candles)
├── data.py             # Data API client (trades, volume, holders)
├── backtest.py         # Data collection engine → EDA/
├── conftest.py         # Pytest fixture for teardown
├── pytest.ini          # asyncio mode config
├── test_connection.py  # Integration tests (require network)
├── EDA/                # Collected datasets + Jupyter notebooks
│   ├── markets.csv     # Master market catalogue
│   ├── <slug>/         # Per-market data directories
│   │   ├── price_history.csv
│   │   └── trades.csv
│   ├── bet_history.csv # Aggregated bet history
│   ├── eda.ipynb
│   ├── bet_positions.ipynb
│   ├── bet_timeline.ipynb
│   ├── maduro_bets.ipynb
│   └── market_analysis.ipynb
├── agent.md            # ← This file
├── plan.md             # Development roadmap
├── architecture.md     # System architecture reference
└── README.md           # User-facing documentation
```

### 3.2 Naming

- **Files**: `snake_case.py` for modules, `snake_case.ipynb` for notebooks.
- **Classes**: `PascalCase` — API clients end in `API` (e.g. `GammaAPI`, `ClobAPI`).
- **Functions**: `snake_case` — async functions prefixed with verbs (`fetch_`, `collect_`, `get_`).
- **Constants**: `UPPER_SNAKE_CASE`.

### 3.3 Dependencies

| Package | Purpose |
|---|---|
| `httpx` | Async HTTP client |
| `polars` | DataFrame operations (preferred over pandas) |
| `matplotlib` | Plotting in notebooks |
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |

> **Note:** `polars` is the project's DataFrame library of choice. Do not introduce `pandas` unless there is a compelling interop reason.

### 3.4 Git Workflow

- Feature branches off `main`.
- Commit messages: `<type>: <description>` where type ∈ {`feat`, `fix`, `refactor`, `docs`, `test`, `data`}.
- EDA datasets (CSVs) **are** committed — they represent the reproducible snapshot.
- Notebooks should be committed with outputs cleared unless the outputs are the primary deliverable (e.g. published analysis).

---

## 4. Testing Policy

- **Integration tests** (`test_connection.py`) hit live Polymarket APIs — they require network access and are inherently non-deterministic.
- Always run integration tests before merging changes to API client modules.
- Future: Add unit tests with mocked responses for deterministic CI.
- `conftest.py` handles graceful teardown of the singleton `AsyncClient`.

---

## 5. Data Collection Rules

1. `backtest.py` is the canonical data collection script. It discovers top-volume political markets via `GammaAPI`, then fetches price history (`ClobAPI`) and trade fills (`DataAPI`) for each.
2. Output structure: `EDA/<market-slug>/price_history.csv` + `trades.csv`.
3. The Data API exposes ≈3,000 most-recent fills per market. For high-volume markets this compresses near resolution — document this limitation in any analysis.
4. Price history uses daily candles from the CLOB API.
5. Always validate timestamps — the API returns Unix seconds; notebooks convert to `Datetime('us')` via `* 1_000_000`.

---

## 6. EDA Notebook Standards

- Each notebook starts with a markdown cell describing its purpose, methodology, and caveats.
- Use `seaborn-v0_8-whitegrid` style with `ggplot` fallback.
- Standard DPI: 110. Font sizes: title 10, labels 9, ticks 7, legend 7.
- Colour palette:
  - BUY / YES: `#2ea043` (green)
  - SELL / NO: `#cf222e` (red)
  - Price: `#0075ca` (blue)
  - Net: `#6e40c9` (purple)
- USDC formatter: `$X.YM` / `$XK` / `$X` based on magnitude.

---

## 7. Security & Ethics

- **No API keys in source** — `.env` file exists at project root; never commit secrets.
- **No insider trading** — The `maduro_bets.ipynb` analysis is forensic/educational. This project must not be used to exploit non-public information.
- **Respect rate limits** — Do not flood Polymarket APIs. Use sensible delays between paginated requests.
- **No real-money trading** without explicit human approval and risk management framework.

---

## 8. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-16 | Use `polars` over `pandas` | Performance on large trade datasets; expressive API |
| 2026-05-16 | Commit EDA CSVs | Reproducibility — API data is ephemeral post-resolution |
| 2026-05-16 | Singleton `AsyncClient` pattern | Connection pooling; clean lifecycle management |
| 2026-05-17 | Bootstrap `agent.md`, `plan.md`, `architecture.md` | Formalise project governance for scaling |
