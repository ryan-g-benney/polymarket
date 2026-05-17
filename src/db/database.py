import duckdb
import polars as pl
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "polymarket.duckdb"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))

def init_db():
    conn = get_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        transaction_hash VARCHAR,
        timestamp BIGINT,
        price DOUBLE,
        size DOUBLE,
        side VARCHAR,
        outcome VARCHAR,
        condition_id VARCHAR,
        date TIMESTAMP,
        PRIMARY KEY (transaction_hash)
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS forensic_metrics (
        condition_id VARCHAR PRIMARY KEY,
        question VARCHAR,
        category VARCHAR,
        yes_area DOUBLE,
        no_area DOUBLE,
        ratio_no_yes DOUBLE,
        alpha_signal DOUBLE,
        direction VARCHAR,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.close()

def save_trades(trades_df: pl.DataFrame):
    if len(trades_df) == 0:
        return
    conn = get_connection()
    # Remove duplicates from the dataframe based on primary key before insertion
    trades_df = trades_df.unique(subset=["transaction_hash"])
    
    # Use DuckDB's insert logic with ON CONFLICT DO NOTHING
    # DuckDB's python client can query polars dataframes directly
    conn.execute("""
    INSERT INTO trades 
    SELECT transaction_hash, timestamp, price, size, side, outcome, condition_id, date
    FROM trades_df
    ON CONFLICT (transaction_hash) DO NOTHING
    """)
    conn.close()

def save_forensic_metrics(metrics: dict):
    conn = get_connection()
    # Using prepared statements
    conn.execute("""
    INSERT INTO forensic_metrics (condition_id, question, category, yes_area, no_area, ratio_no_yes, alpha_signal, direction, computed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT (condition_id) DO UPDATE SET
        yes_area = excluded.yes_area,
        no_area = excluded.no_area,
        ratio_no_yes = excluded.ratio_no_yes,
        alpha_signal = excluded.alpha_signal,
        direction = excluded.direction,
        computed_at = excluded.computed_at
    """, (
        metrics['condition_id'],
        metrics['question'],
        metrics['category'],
        metrics['yes_area'],
        metrics['no_area'],
        metrics['ratio_no_yes'],
        metrics['alpha_signal'],
        metrics['direction']
    ))
    conn.close()
