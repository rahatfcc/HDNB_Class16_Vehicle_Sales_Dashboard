"""Page 4 - Look at the data itself: table, summary, quality notes, CSV export."""
import pandas as pd
import streamlit as st

import utils as u

u.setup_page("Data Explorer", "🔎")
df_all, source = u.load_data()
df = u.sidebar_filters(df_all, source)

st.title("🔎 Data Explorer")
st.caption("Inspect the rows behind every chart and export your filtered slice.")
u.demo_banner(source)

c1, c2, c3 = st.columns(3)
c1.metric("Rows (filtered)", f"{len(df):,}")
c2.metric("Columns", df.shape[1])
c3.metric("Date range", f"{df['saledate'].min():%b %Y} - {df['saledate'].max():%b %Y}")

tab1, tab2, tab3 = st.tabs(["Data", "Summary statistics", "Cleaning & data quality"])

with tab1:
    cols = st.multiselect("Columns to show", df.columns.tolist(),
                          default=["saledate", "year", "make", "model", "body", "odometer", "mmr", "sellingprice"],
                          key="de_cols")
    n = st.slider("Rows to preview", 10, 1000, 100, step=10, key="de_rows")
    shown = df[cols] if cols else df
    st.dataframe(shown.head(n), hide_index=True, use_container_width=True)

    export = shown.head(100_000)
    st.download_button("⬇️ Download filtered data (CSV, max 100,000 rows)",
                       data=export.to_csv(index=False).encode("utf-8"),
                       file_name="vehicle_sales_filtered.csv", mime="text/csv")

with tab2:
    st.markdown("**Numeric columns**")
    st.dataframe(df[["sellingprice", "mmr", "odometer", "condition", "vehicle_age", "price_vs_mmr_pct"]]
                 .describe().T.round(1), use_container_width=True)
    st.markdown("**Text columns**")
    st.dataframe(df[["make", "model", "body", "transmission", "state", "color"]].describe().T, use_container_width=True)

with tab3:
    st.markdown("#### What the cleaning step does to the raw Kaggle file")
    steps = pd.DataFrame({
        "Step": ["Fix data types", "Standardise text", "Parse dates", "Remove impossible values",
                 "Rescale condition", "Create new columns", "Remove duplicates"],
        "What we do": [
            "year, condition, odometer, mmr, sellingprice -> numbers (errors become blank)",
            "Trim spaces, fix upper/lower case, merge variants (vw -> Volkswagen), 'Unknown' for blanks",
            "'Tue Dec 16 2014 12:30:00 GMT-0800 (PST)' -> real date",
            "Drop rows without price / mmr / odometer / date; price < $500; odometer > 500,000 mi (e.g. 999,999 placeholders); invalid state codes",
            "Raw condition mixes a 1-5 and a 10-49 scale -> multiply 1-5 values by 10",
            "vehicle_age, sale_month, price_vs_mmr, price_vs_mmr_pct",
            "drop_duplicates()",
        ],
    })
    st.dataframe(steps, hide_index=True, use_container_width=True)

    st.markdown("#### 'Unknown' values left after cleaning (share of rows)")
    unk = pd.DataFrame({
        "Column": ["make", "model", "body", "transmission"],
        "Unknown %": [(df[c].astype(str).str.lower() == "unknown").mean() * 100 for c in ["make", "model", "body", "transmission"]],
    })
    st.dataframe(unk, hide_index=True, use_container_width=True,
                 column_config={"Unknown %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
    st.caption("Condition is blank for some rows too; those rows are kept and simply ignored in condition charts.")
