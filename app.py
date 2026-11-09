import altair as alt
import pandas as pd
import streamlit as st

# 允许 Altair 处理超过 5000 行的数据集 (mta_tidy_data.csv 约 1.2 万行)
alt.data_transformers.disable_max_rows()

# 设置 Streamlit 页面布局为宽屏
st.set_page_config(layout="wide", page_title="NYC Multimodal Transit Dashboard")
st.title("NYC Multimodal Transit Recovery Dashboard (2020 - 2025)")

# ------------------------------------------------------------------
# 数据加载模块
# ------------------------------------------------------------------
dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

@st.cache_data
def load_data():
    # 读取第一步清洗好的 Tidy Data
    df = pd.read_csv("mta_tidy_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 固定星期的顺序，避免图表按字母排序
    df['Day_of_Week'] = pd.Categorical(df['Day_of_Week'], categories=dow_order, ordered=True)
    return df

df = load_data()

# 定义统一的分类颜色映射 (Gestalt: Similarity)
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

# ==================================================================
# 第三步核心逻辑：定义交互 (Interaction & Linking)
# ------------------------------------------------------------------
# 创建一个基于 X 轴（时间）的框选刷子 (Interval Selection)
time_brush = alt.selection_interval(encodings=['x'], name="brush")

# ==================================================================
# 第二步核心逻辑：构建 3 个视图与视觉编码 (Views & Encodings)
# ------------------------------------------------------------------

# VIEW 1: 时间序列折线图 (Master Longitudinal Trajectory)
# 编码: X=时间, Y=恢复率, Color=交通方式
base_line = alt.Chart(df).mark_line(opacity=0.8).encode(
    x=alt.X('Date:T', title='Date'),
    y=alt.Y('Recovery_Rate:Q', title='Recovery Rate (%)'),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=alt.Legend(title="Transit Mode", orient="bottom", columns=4)),
    tooltip=['Date:T', 'Transit_Mode:N', alt.Tooltip('Recovery_Rate:Q', format='.1f')]
)

# 100% 恢复基准线
baseline_100 = alt.Chart(pd.DataFrame({'y': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(y='y:Q')

# 将刷子绑定到 View 1
# 注：复合视图拼接时使用显式尺寸 (px)，Vega-Lite 规范不支持在 concat 视图内使用 width='container'
view1 = (base_line + baseline_100).add_params(
    time_brush
).properties(
    width=650, height=330,
    title="VIEW 1: Master Longitudinal Trajectory (Drag to select time period)"
)

# VIEW 2: 平均恢复率柱状图 (Selected Period Avg Recovery)
# 编码: X=平均恢复率, Y=交通方式, Color=交通方式
# 交互: 使用 transform_filter(time_brush) 接收 View 1 的过滤信号
base_bar = alt.Chart(df).mark_bar().encode(
    x=alt.X('mean(Recovery_Rate):Q', title='Mean Recovery (%)'),
    y=alt.Y('Transit_Mode:N', sort='-x', title=None),
    color=alt.Color('Transit_Mode:N', scale=mode_colors, legend=None),
    tooltip=['Transit_Mode:N', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush  # <-- 核心联动代码
)

# 辅助基准线：100% 恢复线
baseline_bar = alt.Chart(pd.DataFrame({'x': [100]})).mark_rule(color='red', strokeDash=[4, 4]).encode(x='x:Q')

view2 = (base_bar + baseline_bar).properties(
    width=350, height=330,
    title="VIEW 2: Avg Recovery in Selected Period"
)

# VIEW 3: 星期分布热力图 (Day-of-Week Transit Recovery Matrix)
# 编码: X=星期, Y=交通方式, Color=平均恢复率 (亮度/色相渐变)
# 交互: 同样使用 transform_filter(time_brush)
view3 = alt.Chart(df).mark_rect().encode(
    x=alt.X('Day_of_Week:O', title='Day of Week', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=mode_colors.domain, title=None),
    color=alt.Color('mean(Recovery_Rate):Q', scale=alt.Scale(scheme='viridis'), title='Recovery (%)'),
    tooltip=['Transit_Mode:N', 'Day_of_Week:O', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush  # <-- 核心联动代码
).properties(
    width=1050, height=220,
    title="VIEW 3: Day-of-Week Recovery Matrix (TWaT Patterns)"
)

# ------------------------------------------------------------------
# 渲染页面布局 (Altair Compound Chart)
# ------------------------------------------------------------------
# 关键 Bug 修复说明：
# 在 Vega-Lite 中，基于 transform_filter(time_brush) 的交互联动必须处于同一个图表规范（Compound Chart）内。
# 原先分别调用 st.altair_chart(view1)、st.altair_chart(view2)、st.altair_chart(view3) 会生成三个完全独立的
# 前端画布，导致 View 2 和 View 3 无法获取 brush 信号（甚至报错提示 signal 未定义），联动彻底失效。
# 正确做法：使用 alt.hconcat 和 alt.vconcat 将三个视图拼接为一个复合图表整体渲染。

dashboard = alt.vconcat(
    alt.hconcat(view1, view2),
    view3
).resolve_scale(
    color='independent'
)

st.altair_chart(dashboard)
