import polars as pl

def calculate_money_flow_alpha(trades: pl.DataFrame) -> dict:
    """
    Calculate the net money flow (USDC) alpha signal using the bucketed methodology.
    Returns directional capital accumulation metrics and the 10th-power anomaly ratio.
    """
    if len(trades) == 0:
        return {"yes_area": 0.0, "no_area": 0.0, "ratio_no_yes": float('inf'), "alpha_signal": 0.0, "direction": None}

    trades = trades.with_columns(
        (pl.col('price') * pl.col('size')).alias('usdc_value')
    )
    
    buy_mask  = pl.col('side').str.to_lowercase() == 'buy'
    buys_only = trades.filter(buy_mask)
    
    if len(buys_only) == 0:
        return {"yes_area": 0.0, "no_area": 0.0, "ratio_no_yes": float('inf'), "alpha_signal": 0.0, "direction": None}

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
    
    # Direction is determined by the max accumulated area
    direction = "YES" if yes_area > no_area else "NO"
    
    import math
    
    total_area = yes_area + no_area
    
    # Calculate percentages and ratio
    if total_area > 0:
        yes_pct = yes_area / total_area
        no_pct = no_area / total_area
        
        if no_pct > 0 and yes_pct > 0:
            ratio_no_yes = no_pct / yes_pct
            alpha_signal = abs(math.log10(ratio_no_yes))
        else:
            ratio_no_yes = float('inf') if yes_pct == 0 else 0.0
            alpha_signal = float('inf')
    else:
        ratio_no_yes = float('inf')
        alpha_signal = 0.0

    return {
        "yes_area": yes_area,
        "no_area": no_area,
        "ratio_no_yes": ratio_no_yes,
        "alpha_signal": alpha_signal,
        "direction": direction
    }
