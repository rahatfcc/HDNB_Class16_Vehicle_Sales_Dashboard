"""Page 2 - What drives the selling price?  (distribution, mileage, age, condition, MMR)"""
import pandas as pd
import plotly.express as px
import streamlit as st

import utils as u

u.setup_page("Price Analysis", "💰")
df_all, source = u.load_data()
df = u.sidebar_filters(df_all, source)

st.title("💰 Price Analysis")
st.caption("What do buyers pay - and why?")
u.demo_banner(source)

tab1, tab2, tab3 = st.tabs(["Distribution", "Price drivers", "Price vs. MMR benchmark"])

# ---------- Tab 1: distribution ----------
with tab1:
    a, b = st.columns(2)
    split = a.toggle("Split histogram by transmission", value=False, key="pa_split")
    bins = b.slider("Bins", 20, 100, 50, key="pa_bins")
    fig = px.histogram(df, x="sellingprice", nbins=bins, color="transmission" if split else None,
                       barmode="overlay", opacity=0.75, color_discrete_sequence=[u.PRIMARY, u.HIGHLIGHT, u.MUTED],
                       labels={"sellingprice": "Selling price ($)"}, title="Most vehicles sell at the low end; a long tail of expensive cars")
    fig.add_vline(x=df["sellingprice"].median(), line_dash="dash", line_color=u.HIGHLIGHT,
                  annotation_text=f"Median {u.money(df['sellingprice'].median())}")
    st.plotly_chart(u.style(fig, 400, legend=split), use_container_width=True)

    top_body = u.top_n(df, "body", 8)["body"].tolist()
    box = df[df["body"].isin(top_body)]
    order = box.groupby("body", observed=True)["sellingprice"].median().sort_values(ascending=False).index.tolist()
    fig = px.box(box, x="body", y="sellingprice", points=False, category_orders={"body": order},
                 color_discrete_sequence=[u.PRIMARY], labels={"body": "Body type", "sellingprice": "Selling price ($)"},
                 title="Price spread by body type (top 8 by volume, sorted by median)")
    st.plotly_chart(u.style(fig, 400, legend=False), use_container_width=True)

# ---------- Tab 2: drivers ----------
with tab2:
    st.markdown("**Mileage, age and condition** are the three biggest price levers in the used-car market.")
    s = u.sample_for_plot(df, 4000)
    c1, c2 = st.columns(2)
    fig = px.scatter(s, x="odometer", y="sellingprice", color="vehicle_age", opacity=0.5,
                     color_continuous_scale="Viridis_r", hover_data=["make", "model", "year"],
                     labels={"odometer": "Odometer (miles)", "sellingprice": "Selling price ($)", "vehicle_age": "Age (yrs)"},
                     title="Higher mileage, lower price (random sample of 4,000)")
    c1.plotly_chart(u.style(fig, 420), use_container_width=True)

    by = c2.selectbox("Depreciation curve by", ["(all vehicles)", "body", "transmission", "make"], key="pa_by")
    if by == "(all vehicles)":
        dep = u.depreciation(df)
        fig = px.line(dep, x="vehicle_age", y="avg_price", markers=True, color_discrete_sequence=[u.PRIMARY])
    else:
        keep = u.top_n(df, by, 6)[by].tolist()
        dep = u.depreciation(df[df[by].isin(keep)], by=by)
        fig = px.line(dep, x="vehicle_age", y="avg_price", color=by, markers=True)
    fig.update_layout(title="Average price by vehicle age",
                      xaxis_title="Vehicle age at sale (years)", yaxis_title="Average selling price ($)")
    c2.plotly_chart(u.style(fig, 420, legend=by != "(all vehicles)"), use_container_width=True)

    heat = df[df["vehicle_age"] <= 15]
    fig = px.density_heatmap(heat, x="vehicle_age", y="condition", z="sellingprice", histfunc="avg",
                             nbinsx=16, nbinsy=10, color_continuous_scale="Blues",
                             labels={"vehicle_age": "Vehicle age (years)", "condition": "Condition score (10-50)",
                                     "sellingprice": "Avg price ($)"},
                             title="Average price by age and condition")
    st.plotly_chart(u.style(fig, 420, legend=False), use_container_width=True)

# ---------- Tab 3: MMR ----------
with tab3:
    st.markdown("**MMR** (Manheim Market Report) is the wholesale benchmark. Points above the line sold for *more* than the benchmark.")
    s = u.sample_for_plot(df, 4000, seed=1)
    hi = float(max(s["mmr"].max(), s["sellingprice"].max()))
    fig = px.scatter(s, x="mmr", y="sellingprice", opacity=0.4, color_discrete_sequence=[u.PRIMARY],
                     hover_data=["make", "model", "year"],
                     labels={"mmr": "MMR benchmark ($)", "sellingprice": "Selling price ($)"},
                     title="Selling price vs. MMR (sample of 4,000)")
    fig.add_shape(type="line", x0=0, y0=0, x1=hi, y1=hi, line=dict(color=u.HIGHLIGHT, dash="dash"))
    st.plotly_chart(u.style(fig, 450, legend=False), use_container_width=True)

    a, b = st.columns(2)
    fig = px.histogram(df[df["price_vs_mmr_pct"].between(-40, 40)], x="price_vs_mmr_pct", nbins=60,
                       color_discrete_sequence=[u.PRIMARY],
                       labels={"price_vs_mmr_pct": "Selling price vs. MMR (%)"},
                       title="Most sales land within a few % of the benchmark (shown: -40% to +40%)")
    fig.add_vline(x=0, line_dash="dash", line_color=u.HIGHLIGHT)
    a.plotly_chart(u.style(fig, 360, legend=False), use_container_width=True)

    mk = u.top_n(df, "make", 50)
    mk = mk[mk["vehicles"] >= 100].sort_values("vs_mmr_pct")
    mk = pd.concat([mk.head(5).assign(group="Lowest vs MMR"), mk.tail(5).assign(group="Highest vs MMR")])
    fig = px.bar(mk, x="vs_mmr_pct", y="make", orientation="h", color="group",
                 color_discrete_map={"Lowest vs MMR": u.MUTED, "Highest vs MMR": u.HIGHLIGHT},
                 labels={"vs_mmr_pct": "Average selling price vs. MMR (%)", "make": ""},
                 title="Makes that sell furthest below / above benchmark (100+ sales)")
    b.plotly_chart(u.style(fig, 360), use_container_width=True)
