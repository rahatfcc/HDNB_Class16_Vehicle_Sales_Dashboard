# 🚗 Vehicle Sales Dashboard (Plotly + Streamlit)

An interactive, multi-page dashboard on **552,247 used-vehicle auction sales** (Kaggle: [Vehicle Sales Data](https://www.kaggle.com/datasets/syedanwarafridi/vehicle-sales-data)).
Built for the Data Analytics Career Bootcamp, Class 16: *Python Dashboard & Portfolio Project*.

| Page | Question it answers |
|---|---|
| **Dashboard** (`app.py`) | How big is the market, how is it trending, what drives it? (KPIs · trend · top makes · price by body · depreciation) |
| **1 Market Overview** | Where, when and what sells? (US map · weekly volume · weekday · make → model treemap) |
| **2 Price Analysis** | What drives price? (histogram · box plot · mileage scatter · depreciation · age × condition heatmap · price vs. MMR) |
| **3 Brand Explorer** | How do brands compare, and what is inside one brand? |
| **4 Data Explorer** | What does the data look like, how was it cleaned, and can I export a slice? |

All pages share the **sidebar filters** (sale date, make, body type, transmission, price range).

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The repo already contains `data/vehicle_sales_clean.csv.gz` (the cleaned data, ~15 MB), so it works straight away.
To rebuild it from the raw Kaggle file: put `car_prices.csv` in `data/` and run `python prepare_data.py`.
If neither file exists the app shows synthetic **DEMO** data with a warning banner (never publish insights from it).

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repo (`app.py`, `utils.py`, `demo_data.py`, `pages/`, `data/vehicle_sales_clean.csv.gz`, `requirements.txt`).
2. Sign in at [share.streamlit.io](https://share.streamlit.io) → **New app** → pick the repo → main file `app.py`.
3. Click **Deploy** and put the public link on your CV, LinkedIn and the top of your README.

## Project structure

```
app.py                  home dashboard (4-zone layout: filters · KPIs · trend · breakdowns)
pages/                  one file per page (Streamlit picks them up automatically)
utils.py                cleaning, filters, the "DAX measures" (pandas aggregations), chart helpers
prepare_data.py         raw CSV -> data/vehicle_sales_clean.csv.gz
demo_data.py            synthetic fallback data (same columns as the real file)
data/                   cleaned data (raw file is git-ignored: 88 MB)
```

## Power BI → Python map (slide 14)

| Power BI | Here |
|---|---|
| Card | `st.metric` |
| Slicer | `st.sidebar.multiselect / slider / date_input` in `utils.sidebar_filters` |
| DAX measure | pandas aggregations in `utils.py` (`kpis`, `top_n`, `monthly`, `depreciation`) |
| Report canvas | `st.columns` + `st.plotly_chart` |
| Publish to web | GitHub + Streamlit Community Cloud |

## Data cleaning (what `utils.clean_vehicle_data` does)

558,837 raw rows → **552,247** (6,590 removed, 1.2%).

- **Convert:** numbers stored as text → numbers; `saledate` text (`Tue Dec 16 2014 12:30:00 GMT-0800 (PST)`) → real dates.
- **Correct:** 96 spellings of `make` → 55 (`vw` → Volkswagen, `ford tk` → Ford…); mixed-case `body`; wrong values in `transmission`; odometer placeholders (999,999).
- **Complete:** rows without price / MMR / odometer / date dropped; blank text → `Unknown`.
- **Create:** `vehicle_age`, `sale_month`, `price_vs_mmr`, `price_vs_mmr_pct`.
- **Assumption to verify:** `condition` mixes a 1–5 and a 10–49 scale; 1–5 values are multiplied by 10.
- **Data caveat:** nearly all sales are in **Dec 2014 – Jul 2015**, with a near-empty April 2015. Trend charts hide months under 500 sales; do not read seasonality from this file.

---

## 📁 Portfolio README template (the 7 sections from slide 19)

Copy this into your own repo's README and fill it in.

1. **Problem:** *e.g. A used-car wholesaler wants to know which vehicles sell best, how fast value is lost, and how prices compare with the market benchmark (MMR).*
2. **Data:** Kaggle Vehicle Sales Data, 558,837 rows × 16 columns, auction sales Dec 2014 – Jul 2015.
3. **Cleaning:** see above; add a before/after screenshot of `df.info()` or the missing-value table.
4. **Analysis:** top findings from the notebook (below are the numbers from this dataset; re-check them yourself):
   - Ford is the #1 make (17% of sales); the top 5 makes are 50% of sales.
   - Vehicles lose about 17% of their value in year 1 and about 49% by year 5.
   - Mileage and price are negatively correlated (−0.59); price tracks MMR closely (r = 0.98), averaging 1.1% below it.
5. **Dashboard:** `<your live Streamlit link>` + 2–3 screenshots.
6. **Insights:** 3–5 actionable takeaways, written for a manager, not for a programmer.
7. **Tools:** Python · pandas · matplotlib · seaborn · Plotly · Streamlit · GitHub.

## Ideas to make it your own

- Add a **state × make** heatmap page, or a "which sellers beat MMR" page (the `seller` column is dropped in the clean file; add it back in `CLEAN_COLUMNS`).
- Add a **what-if calculator**: pick make, age and mileage → show the typical price range.
- Add a `st.cache_data` aggregation layer if you load more columns.
