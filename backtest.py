"""Collect backtesting data for the 20 highest-volume closed political markets.

Output — EDA/
  markets.csv              one row per market (metadata + resolution)
  {market-slug}/
    price_history.csv      daily candles: timestamp, price
    trades.csv             fills: side, price, size, timestamp, outcome, tx_hash

Run:
  python backtest.py
"""

import asyncio
import csv
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

from gamma import GammaAPI
from clob import ClobAPI
from data import DataAPI


OUT_DIR = Path("EDA")

QUERIES = [
    "election",
    "president",
    "trump",
    "senate",
    "congress",
    "prime minister",
    "parliament",
    "referendum",
]

_sem = asyncio.Semaphore(8)

MARKETS_FIELDS = [
    "rank", "slug", "question", "resolution",
    "start_date", "end_date", "closed_time",
    "volume_usdc", "volume_clob_usdc",
    "last_trade_price", "best_bid", "best_ask",
    "condition_id", "event_title", "event_slug",
]

PRICE_HISTORY_FIELDS = ["timestamp", "price"]

TRADES_FIELDS = ["side", "price", "size", "timestamp", "outcome", "tx_hash"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(value, default=None):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return default
    return value if value is not None else default


def _resolution(outcomes: list, prices: list) -> str | None:
    for outcome, price in zip(outcomes, prices):
        try:
            if float(price) >= 0.99:
                return outcome
        except (ValueError, TypeError):
            pass
    return None


async def _noop(result=None):
    return result


async def _safe(coro):
    async with _sem:
        try:
            return await coro
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Token-level data
# ---------------------------------------------------------------------------

async def fetch_token(clob: ClobAPI, token_id: str) -> dict:
    buy, sell, mid, spread, last, book, history = await asyncio.gather(
        _safe(clob.get_price(token_id, "BUY")),
        _safe(clob.get_price(token_id, "SELL")),
        _safe(clob.get_midpoint(token_id)),
        _safe(clob.get_spread(token_id)),
        _safe(clob.get_last_trade_price(token_id)),
        _safe(clob.get_order_book(token_id)),
        _safe(clob.get_prices_history(token_id, interval="max", fidelity=1440)),
    )
    return {
        "token_id": token_id,
        "price_history": (history or {}).get("history", []),
        "snapshot": {
            "buy_price":        (buy    or {}).get("price"),
            "sell_price":       (sell   or {}).get("price"),
            "midpoint":         (mid    or {}).get("mid") or (mid or {}).get("midpoint"),
            "bid":              (spread or {}).get("bid"),
            "ask":              (spread or {}).get("ask"),
            "spread":           (spread or {}).get("spread"),
            "last_trade_price": (last   or {}).get("price"),
            "order_book":       book,
        },
    }


# ---------------------------------------------------------------------------
# Market-level data
# ---------------------------------------------------------------------------

async def fetch_market(clob: ClobAPI, data: DataAPI, market: dict, event: dict) -> dict:
    token_ids = _parse(market.get("clobTokenIds"), [])
    outcomes  = _parse(market.get("outcomes"),     [])
    prices    = _parse(market.get("outcomePrices"), [])

    yes_id = token_ids[0] if len(token_ids) > 0 else None
    no_id  = token_ids[1] if len(token_ids) > 1 else None

    condition_id = market.get("conditionId")

    yes_data, no_data = await asyncio.gather(
        fetch_token(clob, yes_id) if yes_id else _noop({}),
        fetch_token(clob, no_id)  if no_id  else _noop({}),
        return_exceptions=True,
    )

    if isinstance(yes_data, Exception): yes_data = {}
    if isinstance(no_data,  Exception): no_data  = {}

    # Paginate historical trades via conditionId — up to 2,000 most-recent fills
    trades = []
    if condition_id:
        try:
            for offset in range(0, 2000, 500):
                page = await data.get_trades(condition_id, limit=500, offset=offset)
                if not page:
                    break
                trades.extend(page)
                if len(page) < 500:
                    break
        except Exception:
            trades = []

    return {
        "meta": {
            "market_id":        market["id"],
            "slug":             market.get("slug"),
            "question":         market.get("question"),
            "condition_id":     market.get("conditionId"),
            "outcomes":         outcomes,
            "resolution":       _resolution(outcomes, prices),
            "start_date":       market.get("startDateIso"),
            "end_date":         market.get("endDateIso"),
            "closed_time":      market.get("closedTime"),
            "volume_usdc":      market.get("volumeNum"),
            "volume_clob_usdc": market.get("volumeClob"),
            "last_trade_price": market.get("lastTradePrice"),
            "best_bid":         market.get("bestBid"),
            "best_ask":         market.get("bestAsk"),
            "event_title":      event.get("title"),
            "event_slug":       event.get("slug"),
        },
        "yes_token": yes_data,
        "no_token":  no_data,
        "trades":    trades,
    }


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_market_csvs(market_dir: Path, result: dict):
    market_dir.mkdir(parents=True, exist_ok=True)

    # price_history.csv — YES token daily candles
    ph = (result.get("yes_token") or {}).get("price_history") or []
    with open(market_dir / "price_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PRICE_HISTORY_FIELDS)
        w.writeheader()
        w.writerows({"timestamp": row["t"], "price": row["p"]} for row in ph)

    # trades.csv
    trades = result.get("trades") or []
    with open(market_dir / "trades.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TRADES_FIELDS)
        w.writeheader()
        for t in trades:
            w.writerow({
                "side":      t.get("side"),
                "price":     t.get("price"),
                "size":      t.get("size"),
                "timestamp": t.get("timestamp"),
                "outcome":   t.get("outcome"),
                "tx_hash":   t.get("transactionHash"),
            })


# ---------------------------------------------------------------------------
# Market discovery
# ---------------------------------------------------------------------------

async def collect_markets(gamma: GammaAPI, n: int = 20) -> list[tuple[dict, dict]]:
    seen: dict[int, tuple[dict, dict]] = {}

    for query in QUERIES:
        events = await gamma.get_events(
            limit=50,
            closed=True,
            title_search=query,
            order="volume",
            ascending=False,
        )
        for event in (events or []):
            for market in event.get("markets", []):
                if not market.get("closed"):
                    continue
                token_ids = _parse(market.get("clobTokenIds"), [])
                outcomes  = _parse(market.get("outcomes"),     [])
                if len(outcomes) != 2 or len(token_ids) != 2:
                    continue
                mid = market["id"]
                if mid not in seen:
                    seen[mid] = (market, event)

    ranked = sorted(seen.values(), key=lambda x: x[0].get("volumeNum") or 0, reverse=True)
    return ranked[:n]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    # Clear previous run's JSON files from EDA root
    if OUT_DIR.exists():
        for f in OUT_DIR.glob("*.json"):
            f.unlink()

    OUT_DIR.mkdir(exist_ok=True)

    async with GammaAPI() as gamma, ClobAPI() as clob, DataAPI() as data:
        print("Searching for closed political markets …")
        pairs = await collect_markets(gamma)
        print(f"Found {len(pairs)} markets. Collecting data …\n")

        markets_rows = []

        for i, (market, event) in enumerate(pairs):
            slug     = market.get("slug") or str(market["id"])
            question = market.get("question") or ""
            print(f"[{i+1:02d}/{len(pairs)}] {question[:72]}")

            try:
                result   = await fetch_market(clob, data, market, event)
                candles  = len((result.get("yes_token") or {}).get("price_history") or [])
                n_trades = len(result.get("trades") or [])
                vol      = market.get("volumeNum") or 0
                meta     = result["meta"]

                write_market_csvs(OUT_DIR / slug, result)
                print(f"        vol=${vol:>14,.0f}  {candles:>4} candles  {n_trades:>3} trades")

                markets_rows.append({
                    "rank":             i + 1,
                    "slug":             slug,
                    "question":         question,
                    "resolution":       meta["resolution"],
                    "start_date":       meta["start_date"],
                    "end_date":         meta["end_date"],
                    "closed_time":      meta["closed_time"],
                    "volume_usdc":      meta["volume_usdc"],
                    "volume_clob_usdc": meta["volume_clob_usdc"],
                    "last_trade_price": meta["last_trade_price"],
                    "best_bid":         meta["best_bid"],
                    "best_ask":         meta["best_ask"],
                    "condition_id":     meta["condition_id"],
                    "event_title":      meta["event_title"],
                    "event_slug":       meta["event_slug"],
                })

            except Exception as e:
                print(f"        ERROR: {e}")

        with open(OUT_DIR / "markets.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MARKETS_FIELDS)
            w.writeheader()
            w.writerows(markets_rows)

    print(f"\nDone. {len(markets_rows)} markets in {OUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
