import polars as pl

df = pl.read_csv('csv/maduro_bets.csv')
buys = df.filter(pl.col('side').str.to_uppercase() == 'BUY')

for mkt in buys['market'].unique():
    subset = buys.filter(pl.col('market') == mkt)
    yes_vol = subset.filter(pl.col('outcome').str.to_uppercase() == 'YES')['size'].sum()
    no_vol = subset.filter(pl.col('outcome').str.to_uppercase() == 'NO')['size'].sum()
    
    yes_usdc = (subset.filter(pl.col('outcome').str.to_uppercase() == 'YES')['size'] * subset.filter(pl.col('outcome').str.to_uppercase() == 'YES')['price']).sum()
    no_usdc = (subset.filter(pl.col('outcome').str.to_uppercase() == 'NO')['size'] * subset.filter(pl.col('outcome').str.to_uppercase() == 'NO')['price']).sum()
    
    print(f"{mkt}:")
    print(f"  YES size: {yes_vol}, NO size: {no_vol}")
    print(f"  YES usdc: {yes_usdc}, NO usdc: {no_usdc}")
