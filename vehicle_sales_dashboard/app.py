"""Home page = the executive dashboard (four-zone layout from Class 16).

    SIDE  : filters (shared by every page)
    TOP   : headline KPIs
    MIDDLE: trend over time
    BOTTOM: breakdowns that explain the trend
Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

import utils as u

u.setup_page("Dashboard", "🚗")
df_all, source = u.load_data()
df = u.sidebar_filters(df_all, source)

st.title("🚗 Vehicle Sales Dashboard")
st.caption("Used-vehicle auction sales  |  Source: Kaggle - Vehicle Sales Data  |  Use the sidebar to slice the data")
u.demo_banner(source)

# ---------- TOP: KPIs (Power BI "card") ----------
k = u.kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Vehicles sold", f"{k['vehicles']:,}")
c2.metric("Total revenue", u.money(k["revenue"]))
c3.metric("Average selling price", u.money(k["avg_price"]))
c4.metric("Price vs. MMR", f"{k['vs_mmr_pct']:+.1f}%", help="Total selling price / total MMR (market benchmark) - 1")

# ---------- MIDDLE: trend ----------
st.subheader("How are sales trending?")
metric_label = st.radio("Metric", ["Revenue", "Vehicles sold", "Average price"], horizontal=True, key="home_metric")
col_map = {"Revenue": "revenue", "Vehicles sold": "vehicles", "Average price": "avg_price"}
m = u.monthly(df)
m = m[m["sale_month"].isin(u.main_months(df))]
fig = px.area(m, x="sale_month", y=col_map[metric_label],
              labels={"sale_month": "Sale month", col_map[metric_label]: metric_label},
              color_discrete_sequence=[u.PRIMARY], title=f"{metric_label} by month")
fig.update_traces(hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra></extra>")
st.plotly_chart(u.style(fig, 340, legend=False), use_container_width=True)
st.caption(u.coverage_note(df))

# ---------- BOTTOM: drivers ----------
st.subheader("What is driving it?")
b1, b2, b3 = st.columns(3)

tm = u.top_n(df, "make", 10).sort_values("vehicles")
fig1 = px.bar(tm, x="vehicles", y="make", orientation="h", color="make",
              color_discrete_map=u.highlight_colors(tm["make"].tolist(), tm["make"].iloc[-1]),
              labels={"vehicles": "Vehicles sold", "make": ""}, title="Top 10 makes by volume",
              hover_data={"avg_price": ":,.0f"})
b1.plotly_chart(u.style(fig1, 380, legend=False), use_container_width=True)

tb = u.top_n(df, "body", 50, by="avg_price")
tb = tb[tb["vehicles"] >= 50].head(10).sort_values("avg_price")
fig2 = px.bar(tb, x="avg_price", y="body", orientation="h", color="body",
              color_discrete_map=u.highlight_colors(tb["body"].tolist(), tb["body"].iloc[-1]),
              labels={"avg_price": "Average selling price ($)", "body": ""},
              title="Average price by body type (50+ sales)")
b2.plotly_chart(u.style(fig2, 380, legend=False), use_container_width=True)

dep = u.depreciation(df)
fig3 = px.line(dep, x="vehicle_age", y="avg_price", markers=True, color_discrete_sequence=[u.PRIMARY],
               labels={"vehicle_age": "Vehicle age at sale (years)", "avg_price": "Average selling price ($)"},
               title="Price falls as vehicles age")
b3.plotly_chart(u.style(fig3, 380, legend=False), use_container_width=True)

# ---------- Insights ----------
with st.container(border=True):
    st.markdown("**Key takeaways (update with your filters)**")
    for line in u.headline_insights(df):
        st.markdown(f"- {line}")

st.info("Use the pages in the left menu for **Market Overview**, **Price Analysis**, **Brand Explorer** and the **Data Explorer**.")
