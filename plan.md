# Plan — Polymarket Trading Harness

> Development roadmap, milestones, and task breakdown.

---

## 1. Vision

Build a production-grade harness for:
1. **Collecting** prediction-market data from Polymarket's public APIs.
2. **Analysing** market microstructure, money flows, and resolution patterns.
3. **Backtesting** quantitative strategies against historical data.
4. **Executing** (future) automated trades via the CLOB API.

---

## 2. Current State (as of 2026-05-17)

### ✅ Completed

| # | Item | Status |
|---|---|---|
| 1 | Base API client (`api.py`) with singleton `AsyncClient` | Done |
| 2 | Gamma API wrapper (`gamma.py`) — markets, events, tags, series | Done |
| 3 | CLOB API wrapper (`clob.py`) — order books, midpoints, spreads, price history | Done |
| 4 | Data API wrapper (`data.py`) — trades, volume, holders, open interest | Done |
| 5 | Data collection engine (`backtest.py`) — top-20 political markets | Done |
| 6 | Integration test suite (`test_connection.py`) | Done |
| 7 | EDA: Market volume & resolution analysis (`eda.ipynb`) | Done |
| 8 | EDA: Bet positions & cumulative flow (`bet_positions.ipynb`) | Done |
| 9 | EDA: Per-market bet timeline & money flow (`bet_timeline.ipynb`) | Done |
| 10 | EDA: Market-by-market influx + insider signal scoring (`market_analysis.ipynb`) | Done |
| 11 | EDA: Maduro capture markets forensic analysis (`maduro_bets.ipynb`) | Done |
| 12 | Project governance bootstrap (`agent.md`, `plan.md`, `architecture.md`) | Done |

### 🔲 Known Gaps

- No unit tests (only live integration tests).
- No CI/CD pipeline.
- No strategy framework or backtesting engine.
- No trading execution layer.
- No risk management or position sizing.
- No alerting or monitoring.
- Data collection limited to ≈3,000 most-recent fills per market (API cap).
- No persistent database — all data in flat CSVs.

---

## 3. Roadmap

### Phase 1 — Foundation Hardening ⬅ _CURRENT_

> Goal: Make the data layer robust, testable, and extensible.

| Task | Priority | Notes |
|---|---|---|
| Add unit tests with mocked HTTP responses | High | Decouple tests from live API availability |
| Add `requirements.txt` / `pyproject.toml` | High | Pin dependency versions for reproducibility |
| Refactor `backtest.py` into a proper data pipeline module | High | Separate concerns: discovery → fetch → store |
| Add structured logging (`logging` module) | Medium | Replace `print()` calls throughout |
| Add retry/backoff to API clients | Medium | Handle transient failures gracefully |
| Implement incremental data collection | Medium | Don't re-fetch unchanged markets |
| Add data validation layer (schema checks on CSVs) | Medium | Catch API format changes early |
| Set up `.gitignore` properly | Low | Exclude `__pycache__`, `.env`, etc. |

### Phase 2 — Data Infrastructure

> Goal: Move from flat files to a queryable store; support historical replay.

| Task | Priority | Notes |
|---|---|---|
| Introduce SQLite or DuckDB as local datastore | High | Structured queries, joins across markets |
| Build continuous data ingestion (scheduled collection) | High | Cron/scheduler-based periodic fetch |
| Historical data backfill from multiple API sources | Medium | Overcome the 3,000-fill limitation |
| Event-driven data pipeline (market open/close events) | Medium | React to Gamma API webhooks if available |
| Data export utilities (Parquet, JSON) | Low | Interop with external tools |

### Phase 3 — Backtesting Engine

> Goal: Simulate strategies against historical data with realistic execution modelling.

| Task | Priority | Notes |
|---|---|---|
| Define strategy interface (`Strategy` ABC) | High | `on_candle()`, `on_trade()`, `on_signal()` |
| Build backtesting event loop | High | Time-ordered event replay |
| Implement basic strategies (momentum, mean-reversion) | High | Validate the framework |
| Slippage & fee modelling | Medium | Realistic P&L accounting |
| Performance metrics (Sharpe, drawdown, win rate) | Medium | Standard quant metrics |
| Strategy parameter optimization | Medium | Grid search / Bayesian optimization |
| Benchmark against buy-and-hold / random | Low | Sanity check |
| Visualization dashboard for backtest results | Low | Interactive plots |

### Phase 4 — Signal & Analysis Framework

> Goal: Build reusable analytical components for market research.

| Task | Priority | Notes |
|---|---|---|
| Insider trading signal detector (generalize `market_analysis.ipynb`) | High | BUY dominance, whale concentration, time spread |
| Market microstructure analysis module | Medium | Bid-ask spread dynamics, order book depth |
| Event-driven signal framework | Medium | News/event → market impact correlation |
| Cross-market correlation analysis | Medium | Portfolio-level insights |
| Automated report generation | Low | Scheduled EDA → PDF/HTML reports |

### Phase 5 — Live Trading (Future)

> Goal: Execute strategies in real-time with proper risk controls.

| Task | Priority | Notes |
|---|---|---|
| Implement CLOB trading endpoints | High | Place/cancel/amend orders |
| Wallet integration (signing, gas management) | High | On-chain settlement |
| Position management & tracking | High | Real-time P&L |
| Risk management framework | Critical | Max position, max loss, circuit breakers |
| Paper trading mode | High | Test execution without real money |
| Monitoring & alerting (Telegram/Discord/email) | Medium | Execution notifications |
| Multi-strategy orchestration | Medium | Run multiple strategies concurrently |

---

## 4. Milestones

| Milestone | Target | Dependencies |
|---|---|---|
| M1: All unit tests passing, deps pinned | Phase 1 complete | — |
| M2: Local DB with continuous ingestion | Phase 2 complete | M1 |
| M3: First backtest with realistic slippage | Phase 3 core complete | M2 |
| M4: Insider signal alerts on new markets | Phase 4 core complete | M2 |
| M5: Paper trading on testnet | Phase 5 core complete | M3 |
| M6: Live trading with risk controls | Phase 5 complete | M5 + manual review |

---

## 5. Open Questions

1. **Database choice** — SQLite (simple, portable) vs DuckDB (columnar, fast analytics) vs PostgreSQL (if we ever go multi-user)?
2. **Scheduling** — Simple cron vs APScheduler vs Celery for continuous data collection?
3. **Strategy language** — Pure Python vs DSL for strategy definition?
4. **Deployment target** — Local-only vs VPS vs cloud functions?
5. **Wallet security** — How to handle private keys for on-chain trading? Hardware wallet? KMS?
6. **Backtesting granularity** — Candle-level vs tick-level replay?
