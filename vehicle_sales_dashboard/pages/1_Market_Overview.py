"""Page 1 - Where and when do vehicles sell?  (geography, seasonality, make/model mix)"""
import plotly.express as px
import streamlit as st

import utils as u

u.setup_page("Market Overview", "🗺️")
df_all, source = u.load_data()
df = u.sidebar_filters(df_all, source)

st.title("🗺️ Market Overview")
st.caption("Where, when and what sells.")
u.demo_banner(source)

# ---------- Geography ----------
st.subheader("Where do vehicles sell?")
measure = st.selectbox("Colour the map by", ["Vehicles sold", "Revenue", "Average price"], key="mo_measure")
col = {"Vehicles sold": "vehicles", "Revenue": "revenue", "Average price": "avg_price"}[measure]
states = u.top_n(df, "state", 100, by="vehicles").rename(columns={"state": "state_code"})

left, right = st.columns([3, 2])
fig = px.choropleth(states, locations="state_code", locationmode="USA-states", color=col, scope="usa",
                    color_continuous_scale="Blues", labels={col: measure, "state_code": "State"},
                    hover_data={"vehicles": ":,", "avg_price": ":,.0f"}, title=f"{measure} by US state")
left.plotly_chart(u.style(fig, 430, legend=False), use_container_width=True)

top_states = states.sort_values(col, ascending=False).head(10).sort_values(col)
fig = px.bar(top_states, x=col, y="state_code", orientation="h", color="state_code",
             color_discrete_map=u.highlight_colors(top_states["state_code"].tolist(), top_states["state_code"].iloc[-1]),
             labels={col: measure, "state_code": ""}, title=f"Top 10 states - {measure.lower()}")
right.plotly_chart(u.style(fig, 430, legend=False), use_container_width=True)
st.caption("Canadian provinces and non-US codes in the raw data are not drawn on the map.")

# ---------- Seasonality ----------
st.subheader("When do vehicles sell?")
s1, s2 = st.columns(2)
wkly = u.weekly(df)
fig = px.line(wkly, x="week", y="vehicles", markers=True, color_discrete_sequence=[u.PRIMARY],
              labels={"week": "Week starting", "vehicles": "Vehicles sold"}, title="Weekly sales volume")
s1.plotly_chart(u.style(fig, 330, legend=False), use_container_width=True)

wk = u.weekday_mix(df)
fig = px.bar(wk, x="weekday", y="vehicles", labels={"weekday": "Day of week", "vehicles": "Vehicles sold"},
             title="Sales by weekday")
fig.update_traces(marker_color=[u.HIGHLIGHT if v == wk["vehicles"].max() else u.MUTED for v in wk["vehicles"]])
s2.plotly_chart(u.style(fig, 330, legend=False), use_container_width=True)
st.caption(u.coverage_note(df))

# ---------- Mix ----------
st.subheader("What sells?")
n_makes = st.slider("Number of makes in the treemap", 5, 20, 12, key="mo_nmakes")
makes = u.top_n(df, "make", n_makes)["make"].tolist()
mm = (df[df["make"].isin(makes)].groupby(["make", "model"], observed=True)
        .agg(vehicles=("sellingprice", "size"), avg_price=("sellingprice", "mean")).reset_index())
mm = mm[mm["vehicles"] >= 20]
fig = px.treemap(mm, path=[px.Constant("All makes"), "make", "model"], values="vehicles",
                 color="avg_price", color_continuous_scale="Blues",
                 labels={"avg_price": "Avg price ($)"}, title="Make -> model: size = volume, colour = average price")
st.plotly_chart(u.style(fig, 520, legend=False), use_container_width=True)

c1, c2 = st.columns(2)
tr = df["transmission"].value_counts().rename_axis("transmission").reset_index(name="vehicles")
fig = px.pie(tr, names="transmission", values="vehicles", hole=0.5, title="Transmission mix",
             color_discrete_sequence=[u.PRIMARY, u.HIGHLIGHT, u.MUTED])
c1.plotly_chart(u.style(fig, 320), use_container_width=True)
yr = df.groupby("year", observed=True).size().rename("vehicles").reset_index()
fig = px.bar(yr, x="year", y="vehicles", color_discrete_sequence=[u.PRIMARY],
             labels={"year": "Model year", "vehicles": "Vehicles sold"}, title="Vehicles sold by model year")
c2.plotly_chart(u.style(fig, 320, legend=False), use_container_width=True)
