import altair as alt
import pandas as pd
import streamlit as st

alt.data_transformers.disable_max_rows()

st.set_page_config(layout="wide", page_title="NYC Multimodal Transit Dashboard")
st.title("NYC Multimodal Transit Recovery Dashboard (2020 - 2025)")

dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

@st.cache_data
def load_data():
    df = pd.read_csv("mta_tidy_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    
    df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=dow_order, ordered=True)
    return df

df = load_data()

mode_colors = alt.Scale(
    domain=[
        'Subways', 'Buses', 'Metro-North', 'LIRR', 
        'Access-A-Ride', 'Bridges and Tunnels', 'Staten Island Railway'
    ],
    range=[
        '#ff7f0e', '#1f77b4', '#aec7e8', '#2ca02c', 
        '#9467bd', '#8c564b', '#e377c2'
    ]
)

time_brush = alt.selection_interval(encodings=['x'], name="brush")
mode_select = alt.selection_point(fields=['Transit_Mode'], name="mode_select")

base_line = alt.Chart(df).mark_line().encode(
    x=alt.X(
        'yearweek(Date):T', 
        title='Date (Weekly)', 
        axis=alt.Axis(format='%Y', tickCount='year', labelAngle=0)
    ),
    y=alt.Y('mean(Recovery_Rate):Q', title='Weekly Avg Recovery Rate (%)'),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=alt.Legend(title="Transit Mode", orient="bottom", columns=4)),
    opacity=alt.condition(mode_select, alt.value(0.9), alt.value(0.12)),
    strokeWidth=alt.condition(mode_select, alt.value(2.2), alt.value(1.0)),
    tooltip=[
        alt.Tooltip('yearweek(Date):T', title='Week of', format='%Y-%m-%d'), 
        'Transit_Mode:N', 
        alt.Tooltip('mean(Recovery_Rate):Q', title='Weekly Avg Recovery (%)', format='.1f')
    ]
)

baseline_100 = alt.Chart(pd.DataFrame({'y': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(y='y:Q')

view1 = (base_line + baseline_100).add_params(
    time_brush
).properties(
    width=650, height=330,
    title="VIEW 1: Master Longitudinal Trajectory (Weekly Avg, Drag to select time period)"
)

base_bar = alt.Chart(df).mark_bar().encode(
    x=alt.X('mean(Recovery_Rate):Q', title='Mean Recovery (%)'),
    y=alt.Y('Transit_Mode:N', sort='-x', title=None),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=None),
    opacity=alt.condition(mode_select, alt.value(1.0), alt.value(0.25)),
    tooltip=['Transit_Mode:N', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush
).add_params(
    mode_select
)

baseline_bar = alt.Chart(pd.DataFrame({'x': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(x='x:Q')

view2 = (base_bar + baseline_bar).properties(
    width=350, height=330,
    title="VIEW 2: Avg Recovery in Selected Period (Click bar to highlight)"
)

heat_rect = alt.Chart(df).mark_rect(stroke='white', strokeWidth=1).encode(
    x=alt.X('Day_of_Week:O', title='Day of Week', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=mode_colors.domain, title=None),
    color=alt.Color(
        'mean(Recovery_Rate):Q', 
        scale=alt.Scale(scheme='redblue', domainMid=100, reverse=True), 
        title='Recovery (%)'
    ),
    opacity=alt.condition(mode_select, alt.value(1.0), alt.value(0.18)),
    tooltip=['Transit_Mode:N', 'Day_of_Week:O', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush
)

heat_text = alt.Chart(df).mark_text(baseline='middle', fontSize=11, fontWeight='bold').encode(
    x=alt.X('Day_of_Week:O', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=mode_colors.domain),
    text=alt.Text('mean(Recovery_Rate):Q', format='.1f'),
    color=alt.condition(
        'datum.mean_Recovery_Rate < 45 || datum.mean_Recovery_Rate > 125',
        alt.value('white'),
        alt.value('black')
    ),
    opacity=alt.condition(mode_select, alt.value(1.0), alt.value(0.2))
).transform_filter(
    time_brush
)

view3 = (heat_rect + heat_text).properties(
    width=1050, height=220,
    title="VIEW 3: Day-of-Week Recovery Matrix (Red: >100%, White: ~100%, Blue: <100%)"
)

dashboard = alt.vconcat(
    alt.hconcat(view1, view2),
    view3
).resolve_scale(
    color='independent'
)

st.altair_chart(dashboard)
