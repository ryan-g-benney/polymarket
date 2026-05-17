import httpx
import polars as pl
from typing import List, Dict, Any

def fetch_all_trades(condition_id: str) -> pl.DataFrame:
    """Fetch up to ~3,000 most-recent fills for a market (API hard cap)."""
    rows, seen = [], set()
    with httpx.Client(base_url='https://data-api.polymarket.com', timeout=30) as client:
        for offset in range(0, 3000, 500):
            try:
                data = client.get('/trades',
                    params={'market': condition_id, 'limit': 500, 'offset': offset}
                ).json()
                if not isinstance(data, list) or not data:
                    break
                for r in data:
                    h = r.get('transactionHash', str(r.get('timestamp','')))
                    if h not in seen:
                        seen.add(h)
                        rows.append(r)
                if len(data) < 500:
                    break
            except Exception:
                break
    if not rows:
        return pl.DataFrame()
    df = pl.DataFrame({
        'transaction_hash': [r.get('transactionHash', '') for r in rows],
        'timestamp': [int(r.get('timestamp', 0))   for r in rows],
        'price':     [float(r.get('price', 0))     for r in rows],
        'size':      [float(r.get('size', 0))      for r in rows],
        'side':      [str(r.get('side', ''))       for r in rows],
        'outcome':   [str(r.get('outcome', ''))    for r in rows],
        'condition_id': condition_id,
    }).sort('timestamp')
    return df.with_columns(
        (pl.col('timestamp') * 1_000_000).cast(pl.Datetime('us')).alias('date')
    )
