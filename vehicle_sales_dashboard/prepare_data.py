"""Clean the raw Kaggle file once and save a smaller, analysis-ready CSV for the app.

    python prepare_data.py                      # uses data/car_prices.csv
    python prepare_data.py --raw path/to.csv    # custom location
    python prepare_data.py --sample 150000      # OPTIONAL: random subset (totals such as "vehicles sold" will then be understated)

Output: data/vehicle_sales_clean.csv.gz  (~15 MB - commit THIS file to GitHub for Streamlit Cloud)
"""
import argparse
import sys
import types

import pandas as pd

# utils.py imports streamlit only for the dashboard; this script does not need it installed
try:
    import streamlit  # noqa: F401
except ImportError:
    stub = types.ModuleType("streamlit")
    stub.cache_data = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
    sys.modules["streamlit"] = stub

import utils as u  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--raw", default=str(u.RAW_CSV), help="path to the raw car_prices.csv")
parser.add_argument("--sample", type=int, default=0, help="keep only this many random rows (0 = all)")
args = parser.parse_args()

raw = pd.read_csv(args.raw)
print(f"Raw rows:   {len(raw):,}")
clean = u.clean_vehicle_data(raw)
print(f"Clean rows: {len(clean):,}  ({len(raw) - len(clean):,} removed)")
if args.sample and args.sample < len(clean):
    clean = clean.sample(args.sample, random_state=42).sort_values("saledate").reset_index(drop=True)
    print(f"Sampled to: {len(clean):,}")
clean.to_csv(u.CLEAN_CSV, index=False)
print(f"Saved {u.CLEAN_CSV}  ({u.CLEAN_CSV.stat().st_size / 1e6:.1f} MB)")
