"""Shared helpers for every page: data loading, cleaning, filters, aggregations, chart helpers.

Chart-ready numbers are computed by small pure-pandas functions (no Streamlit inside),
so they are easy to read, test and reuse in a notebook.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CLEAN_CSV = DATA_DIR / "vehicle_sales_clean.csv.gz"
RAW_CSV = DATA_DIR / "car_prices.csv"

HIGHLIGHT = "#DC143C"   # crimson - the ONE bar we want the reader to notice
MUTED = "#9AA5B1"       # everything else
PRIMARY = "#1F4E79"

# --------------------------------------------------------------------------------------
# 1. CLEANING  (same steps as the notebook, Part 3)
# --------------------------------------------------------------------------------------
MAKE_FIXES = {
    "bmw": "BMW", "gmc": "GMC", "mini": "MINI", "vw": "Volkswagen",
    "mercedes": "Mercedes-Benz", "mercedes-b": "Mercedes-Benz", "landrover": "Land Rover",
    "chev truck": "Chevrolet", "gmc truck": "GMC", "dodge tk": "Dodge",
    "ford tk": "Ford", "ford truck": "Ford", "mazda tk": "Mazda", "hyundai tk": "Hyundai",
}
CLEAN_COLUMNS = [
    "saledate", "sale_month", "year", "make", "model", "body", "transmission", "state",
    "condition", "odometer", "color", "mmr", "sellingprice",
    "vehicle_age", "price_vs_mmr", "price_vs_mmr_pct",
]


def clean_vehicle_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Raw car_prices.csv -> analysis-ready DataFrame."""
    df = raw.copy()

    # numbers stored as text -> numbers (bad values become NaN instead of crashing)
    for col in ["year", "condition", "odometer", "mmr", "sellingprice"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # text columns: trim, fix case, merge spelling variants
    s = df["make"].astype("string").str.strip().str.lower()
    df["make"] = s.map(MAKE_FIXES).fillna(s.str.title()).fillna("Unknown")
    df["model"] = df["model"].astype("string").str.strip().str.title().fillna("Unknown")
    df["body"] = (df["body"].astype("string").str.strip().str.title()
                  .replace({"Suv": "SUV"}).fillna("Unknown"))
    trans = df["transmission"].astype("string").str.strip().str.lower()
    df["transmission"] = trans.where(trans.isin(["automatic", "manual"]), "unknown")
    df["state"] = df["state"].astype("string").str.strip().str.upper()
    df["color"] = df["color"].astype("string").str.strip().str.lower()

    # "Tue Dec 16 2014 12:30:00 GMT-0800 (PST)" -> real date
    date_text = df["saledate"].astype("string").str.extract(r"([A-Z][a-z]{2} \d{1,2} \d{4})")[0]
    df["saledate"] = pd.to_datetime(date_text, format="%b %d %Y", errors="coerce")

    # drop rows we cannot analyse, then impossible values
    df = df.dropna(subset=["sellingprice", "mmr", "odometer", "saledate", "year"])
    df = df[df["state"].str.fullmatch(r"[A-Z]{2}", na=False)]
    df = df[df["sellingprice"].between(500, 250_000) & df["mmr"].between(500, 250_000)]
    df = df[df["odometer"].between(0, 500_000)]
    df = df[df["year"].between(1990, 2015)]

    # condition mixes a 1-5 scale and a 10-49 scale -> put both on 10-50
    df["condition"] = np.where(df["condition"] <= 5, df["condition"] * 10, df["condition"])

    # new columns
    df["vehicle_age"] = (df["saledate"].dt.year - df["year"]).clip(lower=0).astype(int)
    df["sale_month"] = df["saledate"].dt.to_period("M").dt.to_timestamp()
    df["price_vs_mmr"] = df["sellingprice"] - df["mmr"]
    df["price_vs_mmr_pct"] = df["price_vs_mmr"] / df["mmr"] * 100
    df["year"] = df["year"].astype(int)

    df = df[CLEAN_COLUMNS].drop_duplicates().reset_index(drop=True)
    for col in ["make", "model", "body", "transmission", "state", "color"]:
        df[col] = df[col].astype("category")
    return df


@st.cache_data(show_spinner="Loading vehicle sales data...")
def load_data() -> tuple[pd.DataFrame, str]:
    """Return (dataframe, source_label). Order: clean CSV -> raw CSV -> built-in demo data."""
    if CLEAN_CSV.exists():
        df = pd.read_csv(CLEAN_CSV, parse_dates=["saledate", "sale_month"])
        for col in ["make", "model", "body", "transmission", "state", "color"]:
            df[col] = df[col].astype("category")
        return df, "Kaggle: Vehicle Sales Data"
    if RAW_CSV.exists():
        return clean_vehicle_data(pd.read_csv(RAW_CSV)), "Kaggle: Vehicle Sales Data"
    from demo_data import make_demo_raw
    return clean_vehicle_data(make_demo_raw()), "DEMO"


# --------------------------------------------------------------------------------------
# 2. PAGE SETUP + SIDEBAR FILTERS  (Power BI "slicers")
# --------------------------------------------------------------------------------------
def setup_page(title: str, icon: str) -> None:
    st.set_page_config(page_title=f"{title} | Vehicle Sales", page_icon=icon, layout="wide")
    st.markdown(
        """<style>
        [data-testid="stMetric"]{background:rgba(31,78,121,.06);border:1px solid rgba(31,78,121,.18);
            padding:12px 16px;border-radius:10px;}
        [data-testid="stMetricLabel"]{opacity:.75}
        </style>""",
        unsafe_allow_html=True,
    )


def sidebar_filters(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Draw the shared sidebar and return the filtered DataFrame."""
    sb = st.sidebar
    sb.header("Filters")
    d_min, d_max = df["saledate"].min().date(), df["saledate"].max().date()
    picked = sb.date_input("Sale date", value=(d_min, d_max), min_value=d_min, max_value=d_max, key="f_date")
    start, end = (picked if isinstance(picked, (tuple, list)) and len(picked) == 2 else (d_min, d_max))

    makes = sb.multiselect("Make", sorted(df["make"].cat.categories), key="f_make", placeholder="All makes")
    bodies = sb.multiselect("Body type", sorted(df["body"].cat.categories), key="f_body", placeholder="All body types")
    trans = sb.multiselect("Transmission", sorted(df["transmission"].cat.categories), key="f_trans",
                           placeholder="All transmissions")
    p_hi = int(np.ceil(df["sellingprice"].quantile(0.999) / 1000) * 1000)
    price = sb.slider("Selling price ($)", 0, p_hi, (0, p_hi), step=500, key="f_price")

    mask = df["saledate"].between(pd.Timestamp(start), pd.Timestamp(end)) & df["sellingprice"].between(*price)
    if makes:
        mask &= df["make"].isin(makes)
    if bodies:
        mask &= df["body"].isin(bodies)
    if trans:
        mask &= df["transmission"].isin(trans)
    out = df[mask]

    sb.divider()
    sb.caption(f"**{len(out):,}** of {len(df):,} sales match")
    if source == "DEMO":
        sb.warning("Showing synthetic DEMO data. Add the Kaggle file (see README) for real results.")
    if out.empty:
        st.warning("No sales match these filters. Widen the filters in the sidebar.")
        st.stop()
    return out


def demo_banner(source: str) -> None:
    if source == "DEMO":
        st.warning("**Demo data** - these numbers are synthetic. Follow the README to load the real Kaggle dataset.",
                   icon="⚠️")


# --------------------------------------------------------------------------------------
# 3. NUMBERS  (pure pandas = the "DAX measures" of this dashboard)
# --------------------------------------------------------------------------------------
def money(x: float) -> str:
    if abs(x) >= 1e9:
        return f"${x / 1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:.1f}K"
    return f"${x:,.0f}"


def kpis(df: pd.DataFrame) -> dict:
    return {
        "vehicles": len(df),
        "revenue": df["sellingprice"].sum(),
        "avg_price": df["sellingprice"].mean(),
        "vs_mmr_pct": (df["sellingprice"].sum() / df["mmr"].sum() - 1) * 100,
        "median_odometer": df["odometer"].median(),
    }


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    out = (df.groupby("sale_month", observed=True)
             .agg(vehicles=("sellingprice", "size"), revenue=("sellingprice", "sum"),
                  avg_price=("sellingprice", "mean"))
             .reset_index())
    return out


def top_n(df: pd.DataFrame, col: str, n: int = 10, by: str = "vehicles") -> pd.DataFrame:
    g = (df.groupby(col, observed=True)
           .agg(vehicles=("sellingprice", "size"), revenue=("sellingprice", "sum"),
                avg_price=("sellingprice", "mean"), avg_odometer=("odometer", "mean"),
                vs_mmr_pct=("price_vs_mmr_pct", "median"))
           .reset_index())
    return g.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def depreciation(df: pd.DataFrame, by: str | None = None, max_age: int = 20, min_n: int = 30) -> pd.DataFrame:
    keys = ["vehicle_age"] + ([by] if by else [])
    g = (df[df["vehicle_age"] <= max_age].groupby(keys, observed=True)
           .agg(avg_price=("sellingprice", "mean"), vehicles=("sellingprice", "size")).reset_index())
    return g[g["vehicles"] >= min_n]


def main_months(df: pd.DataFrame, min_rows: int = 500) -> list:
    """Months with enough sales to trust. The Kaggle file is lumpy: a few stray 2014 rows and a
    near-empty April 2015 look like market swings but are really data-collection gaps."""
    counts = df.groupby("sale_month", observed=True).size()
    return counts[counts >= min_rows].index.tolist()


def coverage_note(df: pd.DataFrame) -> str:
    months = main_months(df)
    if not months:
        return ""
    return (f"Main sales period: {min(months):%b %Y} - {max(months):%b %Y}. Months with fewer than 500 sales "
            "are hidden from trend charts (they are data-collection gaps, not market drops).")


def weekly(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["sale_month"].isin(main_months(df))]
    g = (d.assign(week=d["saledate"].dt.to_period("W").dt.start_time)
           .groupby("week", observed=True)
           .agg(vehicles=("sellingprice", "size"), revenue=("sellingprice", "sum"), avg_price=("sellingprice", "mean"))
           .reset_index())
    return g


def weekday_mix(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    g = df["saledate"].dt.strftime("%a").value_counts().reindex(order).fillna(0).rename("vehicles")
    return g.rename_axis("weekday").reset_index()


def sample_for_plot(df: pd.DataFrame, n: int = 4000, seed: int = 0) -> pd.DataFrame:
    """Scatter plots with 500k points are slow in a browser - plot a random sample."""
    return df if len(df) <= n else df.sample(n, random_state=seed)


def headline_insights(df: pd.DataFrame) -> list[str]:
    """Plain-English takeaways that update with the filters."""
    k = kpis(df)
    mk = top_n(df, "make", 1).iloc[0]
    body = top_n(df, "body", 50, by="avg_price")
    body = body[body["vehicles"] >= 100]
    m = monthly(df)
    m = m[m["sale_month"].isin(main_months(df))]
    lines = [
        f"**{mk['make']}** is the top make with **{int(mk['vehicles']):,}** sales "
        f"({mk['vehicles'] / len(df):.0%} of the filtered market).",
        f"On average vehicles sold **{k['vs_mmr_pct']:+.1f}%** vs. the MMR (market benchmark) price.",
    ]
    if not body.empty:
        lines.append(f"**{body.iloc[0]['body']}** is the most expensive body type with 100+ sales "
                     f"(avg {money(body.iloc[0]['avg_price'])}).")
    if len(m) > 1:
        peak = m.loc[m["vehicles"].idxmax()]
        lines.append(f"Busiest month: **{peak['sale_month']:%b %Y}** with {int(peak['vehicles']):,} sales.")
    return lines


# --------------------------------------------------------------------------------------
# 4. CHART HELPERS
# --------------------------------------------------------------------------------------
def highlight_colors(values: list, key) -> dict:
    """Map every category to MUTED except `key`, which is crimson (deck rule: highlight one bar)."""
    return {v: (HIGHLIGHT if v == key else MUTED) for v in values}


def style(fig, height: int = 380, legend: bool = True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), showlegend=legend,
                      title=dict(x=0, font=dict(size=16)), template="plotly_white")
    return fig
