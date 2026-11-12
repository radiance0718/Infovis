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

base_line = alt.Chart(df).mark_line(opacity=0.8).encode(
    x=alt.X(
        'Date:T', 
        title='Date', 
        axis=alt.Axis(format='%Y', tickCount='year', labelAngle=0)
    ),
    y=alt.Y('Recovery_Rate:Q', title='Recovery Rate (%)'),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=alt.Legend(title="Transit Mode", orient="bottom", columns=4)),
    tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Transit_Mode:N', alt.Tooltip('Recovery_Rate:Q', format='.1f')]
)

baseline_100 = alt.Chart(pd.DataFrame({'y': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(y='y:Q')

view1 = (base_line + baseline_100).add_params(
    time_brush
).properties(
    width=650, height=330,
    title="VIEW 1: Master Longitudinal Trajectory (Drag to select time period)"
)

base_bar = alt.Chart(df).mark_bar().encode(
    x=alt.X('mean(Recovery_Rate):Q', title='Mean Recovery (%)'),
    y=alt.Y('Transit_Mode:N', sort='-x', title=None),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=None),
    tooltip=['Transit_Mode:N', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush
)

baseline_bar = alt.Chart(pd.DataFrame({'x': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(x='x:Q')

view2 = (base_bar + baseline_bar).properties(
    width=350, height=330,
    title="VIEW 2: Avg Recovery in Selected Period"
)

heat_rect = alt.Chart(df).mark_rect(stroke='white', strokeWidth=1).encode(
    x=alt.X('Day_of_Week:O', title='Day of Week', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=mode_colors.domain, title=None),
    color=alt.Color(
        'mean(Recovery_Rate):Q', 
        scale=alt.Scale(scheme='redyellowgreen', domainMid=100), 
        title='Recovery (%)'
    ),
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
    )
).transform_filter(
    time_brush
)

view3 = (heat_rect + heat_text).properties(
    width=1050, height=220,
    title="VIEW 3: Day-of-Week Recovery Matrix (Green: >100%, Yellow: ~100%, Red: <100%)"
)

dashboard = alt.vconcat(
    alt.hconcat(view1, view2),
    view3
).resolve_scale(
    color='independent'
)

st.altair_chart(dashboard)
