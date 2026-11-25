# Development Log (DEV_LOG)

本文档记录 **NYC Multimodal Transit Recovery Dashboard (2020 - 2025)**（CS 6313 Information Visualization 项目）从初始方案到最终版本的完整迭代过程、遇到的问题与核心修复。

---

## 1. 初始方案（Initial Design & Architecture）

项目采用 **Python + Pandas + Altair (Vega-Lite) + Streamlit** 构建多视图协同可视化（Multiple Coordinated Views, MCV）：

1. **数据预处理（`prepate_mta_data.py` -> `preprocess_mta_data()`）**
   - 读取原始宽表 `MTA_Daily_Ridership_Data__2020_-_2025_20261013.csv`，清洗千分位逗号与百分号；
   - 使用 `pd.melt` / 遍历映射将其转换为 Tidy Long Format 并导出为 `mta_tidy_data.csv`（共 12,432 行，5 列：`Date`、`Day_of_Week`、`Ridership_Volume`、`Recovery_Rate`、`Transit_Mode`）。
2. **三视图初始设计（`app.py`）**
   - **数据加载**：`load_data()` 读取 `mta_tidy_data.csv`，解析日期并设置 `Day_of_Week` 为有序分类变量。
   - **VIEW 1（主时间序列折线图）**：展示 7 种交通方式的**每日**恢复率曲线 + 100% 红色基准线 `baseline_100`，绑定时间区间刷子 `time_brush = alt.selection_interval(encodings=['x'], name="brush")`。
   - **VIEW 2（平均恢复率柱状图）**：按选中时段均值降序排列各交通方式，通过 `.transform_filter(time_brush)` 联动。
   - **VIEW 3（星期分布热力图）**：使用 `viridis` 单向顺序色阶展示星期几与交通方式的交叉均值矩阵，通过 `.transform_filter(time_brush)` 联动。
   - **页面布局**：使用 Streamlit 的 `st.columns([2, 1])` 放置 `view1` 与 `view2`，下方单独调用 `st.altair_chart(view3, use_container_width=True)`。

---

## 2. 迭代过程中遇到的问题与 Bug

在测试与使用过程中，陆续发现并解决了以下 7 类核心问题：

1. **致命 Bug — 跨视图交互联动彻底失效**
   - **原因**：原先分别调用 3 次 `st.altair_chart(view1)`、`st.altair_chart(view2)`、`st.altair_chart(view3)`，在前端生成了 3 个相互隔离的 Vega 实例。`view2` 与 `view3` 的 `.transform_filter(time_brush)` 引用了未在本图定义的参数 `brush`，导致拖拽 `view1` 时其余视图完全无响应。
2. **复合视图尺寸不兼容与 API 弃用警告**
   - **原因**：Vega-Lite 规范不支持在 `hconcat` / `vconcat` 复合视图内部使用 `width='container'`；此外新版 Streamlit 中 `use_container_width=True` 已触发弃用警告。
3. **图层继承错误透明度条件（`baseline_100` 变暗）**
   - **原因**：最初在 `(base_line + baseline_100)` 图层顶层调用 `.encode(opacity=alt.condition(time_brush, ...))`。由于 `baseline_100` 的数据源仅包含 `{'y': [100]}` 而无 `Date` 字段，始终判定为未选中而被错误淡化；同时连续 `mark_line` 无法按数据点分段设置透明度。
4. **热力图星期顺序错乱**
   - **原因**：Vega-Lite 不自动继承 Pandas 的 `CategoricalDtype` 顺序，在 `view3` 中设置 `sort=None` 后，X 轴按数据首行自然出现顺序排列（`2020-03-01` 为 `Sun`，导致从周日而非周一开始）。
5. **Altair 默认 5,000 行上限 (`MaxRowsError`)**
   - **原因**：`mta_tidy_data.csv` 包含 12,432 行数据，在直接调用 `.to_dict()` / `.to_html()` 序列化或本地校验时触发 `MaxRowsError`。
6. **View 1 刻度显示月份且日级曲线锯齿过重**
   - **原因**：默认时间轴刻度在约 5 年跨度下自动显示 `April`、`July` 等月份而非年份；每日数据受工作日与周末客流差异影响，折线呈高频锯齿震荡，不利于观察长期趋势。
7. **View 3 对 >100% 场景表达不足及色盲/注释问题**
   - **原因**：2024–2025 年部分模式（如 `Access-A-Ride`、`LIRR` 周末）恢复率频繁超过 100%，单向 `viridis` 色阶缺乏 100% 基准分水岭；尝试 `redyellowgreen` 后存在红绿色盲障碍；更换为 `redblue`（配合 `reverse=True`）后，初始标题把红蓝含义写反。

---

## 3. 关键修改记录（附文件名与核心变量/函数）

| 阶段 | 修改目标 | 修改文件 | 核心函数 / 变量 | 关键改动说明 |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | 修复核心联动与视图 Bug | `app.py` | `alt.data_transformers.disable_max_rows()`, `load_data()`, `view1`, `view2`, `view3`, `dashboard` | 1. 启用 `disable_max_rows()` 解除 5000 行限制；<br>2. 使用 `alt.vconcat(alt.hconcat(view1, view2), view3).resolve_scale(color='independent')` 合并为单一复合图表 `dashboard` 并统一由 `st.altair_chart(dashboard)` 渲染，使 `time_brush` 提升为全局共享信号；<br>3. 移除 `view1` 顶层错误的 `opacity` 条件，为 `view2` 增加 `baseline_bar`（100% 基准线）；<br>4. 在 `view3` 显式传入 `sort=dow_order` 与 `sort=mode_colors.domain`；<br>5. 将 `width='container'` 替换为显式像素尺寸（650 / 350 / 1050）。 |
| **Stage 2** | 补充文档与依赖清单 | `README.md`, `requirements.txt` | — | 新增英文项目文档（包含 Overview、Requirements、How to Run、Project Structure、Interaction Guide）及 Python 依赖清单。 |
| **Stage 3** | View 1 轴刻度与周平均聚合 | `app.py`, `README.md` | `base_line`, `view1` | 1. 为 `base_line` 的 X 轴添加 `axis=alt.Axis(format='%Y', tickCount='year', labelAngle=0)`，固定按年份水平显示；<br>2. 将时间编码改为 `'yearweek(Date):T'`、Y 轴改为 `'mean(Recovery_Rate):Q'`，在保留底层日级数据供 View 3 使用的同时，将 View 1 折线平滑为每周均值；<br>3. 更新 Tooltip 为 `Week of`（`%Y-%m-%d`）。 |
| **Stage 4** | View 3 >100% 应对、色盲友好配色与注释修正 | `app.py`, `README.md` | `heat_rect`, `heat_text`, `view3` | 1. 将 `view3` 拆分为 `heat_rect + heat_text` 双图层，叠加精确的百分比数值（`.1f`）与自适应黑白文字对比度条件；<br>2. 采用色盲友好的发散色阶 `alt.Scale(scheme='redblue', domainMid=100, reverse=True)`，以 100% 为中性白锚点；<br>3. 修正 `view3` 标题与 `README.md` 描述，使颜色注释与实际渲染一致（`Red: >100%, White: ~100%, Blue: <100%`）。 |
| **Stage 5** | View 2 反向高亮 View 1 与 View 3 | `app.py` | `mode_select`, `base_bar`, `base_line`, `heat_rect`, `heat_text` | 新增 `mode_select = alt.selection_point(fields=['Transit_Mode'], name="mode_select")` 并绑定到 `base_bar`；同时在 `base_line`（`opacity` 与 `strokeWidth`）以及 `heat_rect`、`heat_text`（`opacity`）接入 `alt.condition(mode_select, ...)`，实现点击柱状图同步高亮折线与热力图对应行。 |

---

## 4. 最终实现的效果

经过上述迭代，最终版本的 `app.py` 实现了流畅、精准且符合信息可视化规范的双向交互仪表盘：

1. **时间维度双向平滑探索（View 1 $\rightarrow$ View 2 & View 3）**：
   - **View 1** 以清晰的年份刻度展示 2020–2025 年各交通方式的**周平均恢复率**平滑轨迹，并附带 100% 红色基准虚线；
   - 鼠标在 View 1 上拖拽框选任意时间窗口，**View 2**（柱状图排名）与 **View 3**（星期热力图与单元格数值）在浏览器端 60fps 实时重算并联动更新。
2. **交通方式跨视图聚焦对比（View 2 $\rightarrow$ View 1 & View 3）**：
   - 点击 **View 2** 中的任意柱状图（支持 `Shift` 多选），**View 1** 中对应交通方式的曲线立即高亮加粗，**View 3** 中对应整行保持高亮，其余交通方式的曲线、柱状图与热力图行自动暗淡，点击空白处即可一键重置。
3. **直观且无障碍的阈值感知（View 3）**：
   - 采用色盲友好的 `redblue` 发散色阶锚定 100% 基准（红色代表超出 100%，白色代表接近 100%，蓝色代表低于 100%），结合单元格内加粗显示的精确均值和周一至周日固定排序，清晰呈现疫情后如 **TWaT（周二至周四通勤高峰）** 与周末恢复差异。
