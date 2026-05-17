import json
from pathlib import Path
from src.ingestion.trades import fetch_all_trades
from src.analysis.money_flow import calculate_money_flow_alpha
from src.db.database import init_db, save_trades, save_forensic_metrics

def main():
    print("Initializing database...")
    init_db()

    markets_file = Path(__file__).parent.parent / "markets.json"
    with open(markets_file, "r") as f:
        markets = json.load(f)

    # Threshold for High Conviction (1.0 = 10x accumulation)
    HIGH_CONVICTION_THRESHOLD = 1.0

    for mkt in markets:
        q = mkt['question']
        cid = mkt['condition_id']
        cat = mkt['category']
        
        print(f"\nProcessing: {q}")
        print("Fetching trades...")
        trades = fetch_all_trades(cid)
        
        print(f"Fetched {len(trades)} trades. Saving to DB...")
        save_trades(trades)
        
        print("Calculating money flow alpha...")
        metrics = calculate_money_flow_alpha(trades)
        
        # Prepare metrics for DB
        db_metrics = {
            "condition_id": cid,
            "question": q,
            "category": cat,
            **metrics
        }
        
        print("Saving forensic metrics to DB...")
        save_forensic_metrics(db_metrics)

        print(f"Results for {q}:")
        print(f"  YES Area: {metrics['yes_area']:,.0f}")
        print(f"  NO Area: {metrics['no_area']:,.0f}")
        print(f"  Direction: {metrics['direction']}")
        print(f"  Ratio (NO/YES): {metrics['ratio_no_yes']:,.4f}")
        print(f"  Alpha Signal: {metrics['alpha_signal']:,.4e}")
        if metrics['alpha_signal'] > HIGH_CONVICTION_THRESHOLD:
            print("  *** HIGH CONVICTION INSIDER ACTIVITY DETECTED ***")

if __name__ == "__main__":
    main()
