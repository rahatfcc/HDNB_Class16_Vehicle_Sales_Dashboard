"""Page 3 - Compare brands, then drill into one."""
import pandas as pd
import plotly.express as px
import streamlit as st

import utils as u

u.setup_page("Brand Explorer", "🏷️")
df_all, source = u.load_data()
df = u.sidebar_filters(df_all, source)

st.title("🏷️ Brand Explorer")
st.caption("Compare makes side by side, then drill into one.")
u.demo_banner(source)

# ---------- Compare ----------
st.subheader("Compare makes")
ranked = u.top_n(df, "make", 200)
default = ranked["make"].head(5).tolist()
chosen = st.multiselect("Makes to compare", ranked["make"].tolist(), default=default, key="be_makes")
if not chosen:
    st.info("Pick at least one make.")
    st.stop()

sub = df[df["make"].isin(chosen)]
summary = u.top_n(sub, "make", len(chosen))
st.dataframe(
    summary.rename(columns={"make": "Make", "vehicles": "Vehicles", "revenue": "Revenue", "avg_price": "Avg price",
                            "avg_odometer": "Avg odometer", "vs_mmr_pct": "vs MMR (%)"}),
    hide_index=True, use_container_width=True,
    column_config={
        "Vehicles": st.column_config.NumberColumn(format="%d"),
        "Revenue": st.column_config.NumberColumn(format="$%d"),
        "Avg price": st.column_config.NumberColumn(format="$%d"),
        "Avg odometer": st.column_config.NumberColumn(format="%d mi"),
        "vs MMR (%)": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

a, b = st.columns(2)
fig = px.bar(summary.sort_values("avg_price", ascending=False), x="make", y="avg_price", color="make",
             labels={"make": "", "avg_price": "Average selling price ($)"}, title="Average selling price")
a.plotly_chart(u.style(fig, 360, legend=False), use_container_width=True)

dep = u.depreciation(sub, by="make", min_n=20)
fig = px.line(dep, x="vehicle_age", y="avg_price", color="make", markers=True,
              labels={"vehicle_age": "Vehicle age (years)", "avg_price": "Average selling price ($)"},
              title="Which brands hold their value?")
b.plotly_chart(u.style(fig, 360), use_container_width=True)

vol = (sub[sub["sale_month"].isin(u.main_months(df))].groupby(["sale_month", "make"], observed=True).size().rename("vehicles").reset_index())
fig = px.line(vol, x="sale_month", y="vehicles", color="make",
              labels={"sale_month": "Sale month", "vehicles": "Vehicles sold"}, title="Monthly volume by make")
st.plotly_chart(u.style(fig, 360), use_container_width=True)
st.caption(u.coverage_note(df))

# ---------- Drill-down ----------
st.subheader("Drill into one make")
one = st.selectbox("Make", chosen, key="be_one")
d = df[df["make"] == one]
k = u.kpis(d)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Vehicles sold", f"{k['vehicles']:,}")
c2.metric("Revenue", u.money(k["revenue"]))
c3.metric("Avg price", u.money(k["avg_price"]))
c4.metric("Median odometer", f"{k['median_odometer']:,.0f} mi")

x, y = st.columns(2)
models = u.top_n(d, "model", 10).sort_values("vehicles")
fig = px.bar(models, x="vehicles", y="model", orientation="h", color="model",
             color_discrete_map=u.highlight_colors(models["model"].tolist(), models["model"].iloc[-1]),
             hover_data={"avg_price": ":,.0f"}, labels={"vehicles": "Vehicles sold", "model": ""},
             title=f"Top models - {one}")
x.plotly_chart(u.style(fig, 400, legend=False), use_container_width=True)

fig = px.violin(d[d["model"].isin(models["model"])], x="model", y="sellingprice", box=True, points=False,
                category_orders={"model": models["model"].tolist()[::-1]}, color_discrete_sequence=[u.PRIMARY],
                labels={"model": "", "sellingprice": "Selling price ($)"}, title=f"Price spread by model - {one}")
y.plotly_chart(u.style(fig, 400, legend=False), use_container_width=True)
