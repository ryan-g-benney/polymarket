import sys
import polars as pl
import numpy as np
import json
import httpx
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

nb = json.load(open('insider_trading_nyt.ipynb', 'r', encoding='utf-8'))
exec(''.join(nb['cells'][1]['source']))
exec(''.join(nb['cells'][2]['source']))
exec(''.join(nb['cells'][3]['source']))

for mkt in MARKETS:
    q = mkt['question']
    cid = mkt['condition_id']
    cat = mkt['category']
    
    print(f"\n--- {q} ---")
    trades = fetch_all_trades(cid)
    
    if len(trades) == 0:
        continue
        
    trades = trades.with_columns(
        (pl.col('price') * pl.col('size')).alias('usdc_value')
    )
    
    buy_mask  = pl.col('side').str.to_lowercase() == 'buy'
    buys_only = trades.filter(buy_mask)
    
    ts_min = trades['timestamp'].min()
    ts_max = trades['timestamp'].max()
    span_s = ts_max - ts_min
    
    NICE = [60, 300, 600, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400]
    raw_b = max(span_s / 30, 60)
    bucket_secs = min(NICE, key=lambda x: abs(x - raw_b))
    
    buys_b = buys_only.with_columns(
        ((pl.col('timestamp') // bucket_secs) * bucket_secs).alias('bucket_ts')
    )
    yes_b = (buys_b.filter(pl.col('outcome').str.to_lowercase() == 'yes')
             .group_by('bucket_ts').agg(pl.col('usdc_value').sum().alias('yes_vol'))
             .sort('bucket_ts'))
    no_b  = (buys_b.filter(pl.col('outcome').str.to_lowercase() == 'no')
             .group_by('bucket_ts').agg(pl.col('usdc_value').sum().alias('no_vol'))
             .sort('bucket_ts'))

    all_ts = sorted(set(yes_b['bucket_ts'].to_list() + no_b['bucket_ts'].to_list()))
    yes_map = dict(zip(yes_b['bucket_ts'].to_list(), yes_b['yes_vol'].to_list()))
    no_map  = dict(zip(no_b['bucket_ts'].to_list(),  no_b['no_vol'].to_list()))

    yes_vals     = [yes_map.get(t, 0.0) for t in all_ts]
    no_vals      = [no_map.get(t,  0.0) for t in all_ts]
    net_vals     = [y - n for y, n in zip(yes_vals, no_vals)]
    
    # Calculate area (sum of net vals where > 0 vs < 0)
    yes_area = sum(v for v in net_vals if v > 0)
    no_area = sum(-v for v in net_vals if v < 0)
    
    print(f"YES area: {yes_area:,.0f}")
    print(f"NO area: {no_area:,.0f}")
    
    if yes_area > 0:
        ratio = no_area / yes_area
        print(f"Ratio (NO/YES): {ratio:,.4f}")
        print(f"Ratio ^ 10: {abs(ratio)**10:,.4f}")
    else:
        print("Ratio: infinity")

    # What if it's the raw volume of yes and no?
    yes_vol = buys_only.filter(pl.col('outcome').str.to_lowercase() == 'yes')['usdc_value'].sum()
    no_vol = buys_only.filter(pl.col('outcome').str.to_lowercase() == 'no')['usdc_value'].sum()
    print(f"Total BUY YES (USDC): {yes_vol:,.0f}")
    print(f"Total BUY NO (USDC): {no_vol:,.0f}")
