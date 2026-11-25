import json
import altair as alt
import pandas as pd
import streamlit as st

alt.data_transformers.disable_max_rows()

st.set_page_config(layout="wide", page_title="NYC Multimodal Transit Dashboard")
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("NYC Multimodal Transit Recovery Dashboard (2020 - 2025)")

# 初始化用于重置 Altair 前端选区的计数器
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

col_tip, col_reset = st.columns([6, 1])
with col_tip:
    st.caption("Tip: Drag on View 1 to select a time period; click bars in View 2 to multi-select transit modes.")
with col_reset:
    if st.button("🔄 Reset", help="Reset all time brush and transit mode selections"):
        st.session_state.reset_counter += 1

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
# toggle=True 允许直接点击多选/取消选中交通方式，无需按住 Shift
mode_select = alt.selection_point(fields=['Transit_Mode'], name="mode_select", toggle=True)

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
    title="VIEW 2: Avg Recovery in Selected Period (Click bars to multi-select)"
)

# 与 View 2 的 sort='-x' 保持完全一致的纵轴排序规则（按平均恢复率降序）
y_mode_sort = alt.EncodingSortField(field='Recovery_Rate', op='mean', order='descending')

heat_rect = alt.Chart(df).mark_rect(stroke='white', strokeWidth=1).encode(
    x=alt.X('Day_of_Week:O', title='Day of Week', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=y_mode_sort, title=None),
    color=alt.Color(
        'mean(Recovery_Rate):Q', 
        scale=alt.Scale(scheme='redblue', domainMid=100, reverse=True), 
        title='Recovery (%)'
    ),
    tooltip=['Transit_Mode:N', 'Day_of_Week:O', alt.Tooltip('mean(Recovery_Rate):Q', format='.1f')]
).transform_filter(
    time_brush
).transform_filter(
    mode_select
)

heat_text = alt.Chart(df).mark_text(baseline='middle', fontSize=11, fontWeight='bold').encode(
    x=alt.X('Day_of_Week:O', sort=dow_order),
    y=alt.Y('Transit_Mode:N', sort=y_mode_sort),
    text=alt.Text('mean(Recovery_Rate):Q', format='.1f'),
    color=alt.condition(
        'datum.mean_Recovery_Rate < 45 || datum.mean_Recovery_Rate > 125',
        alt.value('white'),
        alt.value('black')
    )
).transform_filter(
    time_brush
).transform_filter(
    mode_select
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

# ------------------------------------------------------------------
# 响应式 100% 宽度渲染 (解决 Vega-Lite 复合图表不支持 width='container' 的限制)
# ------------------------------------------------------------------
spec_dict = dashboard.to_dict()
spec_json = json.dumps(spec_dict)

responsive_html = f"""
<!-- reset_counter: {st.session_state.reset_counter} -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      overflow-x: hidden;
      background: transparent;
    }}
    #vis-container {{
      width: 100%;
    }}
  </style>
</head>
<body>
  <div id="vis-container"></div>
  <script>
    const baseSpec = {spec_json};
    const container = document.getElementById('vis-container');
    let resizeTimer = null;
    let lastIsDark = null;

    function detectDarkMode() {{
      try {{
        const parentDoc = window.parent && window.parent.document;
        if (parentDoc) {{
          const appEl = parentDoc.querySelector('.stApp') || parentDoc.body || parentDoc.documentElement;
          const bg = window.parent.getComputedStyle(appEl).backgroundColor;
          const match = bg && bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
          if (match) {{
            const r = parseInt(match[1], 10);
            const g = parseInt(match[2], 10);
            const b = parseInt(match[3], 10);
            const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
            return luminance < 128;
          }}
        }}
      }} catch (e) {{
        // 跨域或沙箱受限时回退到系统主题
      }}
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }}

    function renderResponsive() {{
      const availW = container.clientWidth || window.innerWidth;
      const isDark = detectDarkMode();
      lastIsDark = isDark;

      const fgColor = isDark ? '#fafafa' : '#31333f';
      const gridColor = isDark ? 'rgba(250, 250, 250, 0.15)' : 'rgba(49, 51, 63, 0.15)';
      const domainColor = isDark ? 'rgba(250, 250, 250, 0.4)' : 'rgba(49, 51, 63, 0.4)';

      // 扣除坐标轴标签、图例与间距后，按比例动态分配三视图宽度以占满 100% 横向空间
      const topPlotW = Math.max(480, availW - 245);
      const v1W = Math.floor(topPlotW * 0.66);
      const v2W = Math.floor(topPlotW * 0.34);
      const v3W = Math.max(480, availW - 235);

      const spec = JSON.parse(JSON.stringify(baseSpec));
      spec.background = 'transparent';
      spec.vconcat[0].hconcat[0].width = v1W;
      spec.vconcat[0].hconcat[1].width = v2W;
      spec.vconcat[1].width = v3W;

      // 根据日间/夜间主题调整热力图单元格分隔线颜色
      if (spec.vconcat[1].layer && spec.vconcat[1].layer[0] && spec.vconcat[1].layer[0].mark) {{
        spec.vconcat[1].layer[0].mark.stroke = isDark ? '#0e1117' : '#ffffff';
      }}

      // 注入适配日间/夜晚主题的坐标轴、标题与图例配色
      spec.config = {{
        ...(spec.config || {{}}),
        view: {{ ...((spec.config && spec.config.view) || {{}}), stroke: 'transparent' }},
        title: {{ color: fgColor, subtitleColor: fgColor }},
        axis: {{
          labelColor: fgColor,
          titleColor: fgColor,
          gridColor: gridColor,
          domainColor: domainColor,
          tickColor: domainColor
        }},
        legend: {{
          labelColor: fgColor,
          titleColor: fgColor
        }}
      }};

      vegaEmbed('#vis-container', spec, {{
        actions: {{ export: true, source: false, compiled: false, editor: false }},
        renderer: 'canvas',
        theme: isDark ? 'dark' : undefined
      }}).catch(console.error);
    }}

    renderResponsive();
    window.addEventListener('resize', () => {{
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(renderResponsive, 150);
    }});

    // 实时监听 Streamlit 主题切换（Light / Dark）或系统主题变化
    setInterval(() => {{
      const currentDark = detectDarkMode();
      if (currentDark !== lastIsDark) {{
        renderResponsive();
      }}
    }}, 300);
  </script>
</body>
</html>
"""

st.iframe(responsive_html, width="stretch", height=740)
