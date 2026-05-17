import sys
import polars as pl
import numpy as np
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

df = pl.read_csv('csv/maduro_bets.csv')
buys = df.filter(pl.col('side').str.to_uppercase() == 'BUY')
buys = buys.with_columns((pl.col('price') * pl.col('size')).alias('usdc_value'))

def calc_panel3(market_name):
    print(f"--- {market_name} ---")
    trades = buys.filter(pl.col('market') == market_name)
    if len(trades) == 0:
        return
        
    ts_min = trades['timestamp'].min()
    ts_max = trades['timestamp'].max()
    span_s = ts_max - ts_min
    
    NICE = [60, 300, 600, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400]
    raw_b = max(span_s / 30, 60)
    bucket_secs = min(NICE, key=lambda x: abs(x - raw_b))
    
    buys_b = trades.with_columns(
        ((pl.col('timestamp') // bucket_secs) * bucket_secs).alias('bucket_ts')
    )
    yes_b = (buys_b.filter(pl.col('outcome').str.to_uppercase() == 'YES')
             .group_by('bucket_ts').agg(pl.col('usdc_value').sum().alias('yes_vol'))
             .sort('bucket_ts'))
    no_b  = (buys_b.filter(pl.col('outcome').str.to_uppercase() == 'NO')
             .group_by('bucket_ts').agg(pl.col('usdc_value').sum().alias('no_vol'))
             .sort('bucket_ts'))

    all_ts = sorted(set(yes_b['bucket_ts'].to_list() + no_b['bucket_ts'].to_list()))
    yes_map = dict(zip(yes_b['bucket_ts'].to_list(), yes_b['yes_vol'].to_list()))
    no_map  = dict(zip(no_b['bucket_ts'].to_list(),  no_b['no_vol'].to_list()))

    yes_vals     = [yes_map.get(t, 0.0) for t in all_ts]
    no_vals      = [no_map.get(t,  0.0) for t in all_ts]
    net_vals     = [y - n for y, n in zip(yes_vals, no_vals)]
    
    # "Area" could be sum of positive net flows and sum of negative net flows?
    yes_area = sum(v for v in net_vals if v > 0)
    no_area = sum(-v for v in net_vals if v < 0)
    
    print("YES area:", yes_area)
    print("NO area:", no_area)

for m in df['market'].unique().to_list():
    calc_panel3(m)
