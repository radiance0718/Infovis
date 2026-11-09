import os
import pandas as pd

def preprocess_mta_data():
    input_file = "MTA_Daily_Ridership_Data__2020_-_2025_20261013.csv"
    output_file = "mta_tidy_data.csv"

    if not os.path.exists(input_file):
        print(f"❌ 找不到文件: {input_file}")
        return

    print("正在读取并清洗数据，请稍候...")
    df = pd.read_csv(input_file)

    # 1. 转换日期并提取星期几 (Day of Week)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    df['Day_of_Week'] = df['Date'].dt.strftime('%a')
    
    # 2. 清洗带有逗号和百分号的数字字符串
    # 排除 Date 和 Day_of_Week 列，其余全部去除 "," 和 "%" 并转换为 float
    for col in df.columns:
        if col not in ['Date', 'Day_of_Week']:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. 映射真实 CSV 中的宽表列名
    modes_mapping = {
        'Subways': (
            'Subways: Total Estimated Ridership', 
            'Subways: % of Comparable Pre-Pandemic Day'
        ),
        'Buses': (
            'Buses: Total Estimated Ridership', 
            'Buses: % of Comparable Pre-Pandemic Day'
        ),
        'LIRR': (
            'LIRR: Total Estimated Ridership', 
            'LIRR: % of Comparable Pre-Pandemic Day'
        ),
        'Metro-North': (
            'Metro-North: Total Estimated Ridership', 
            'Metro-North: % of Comparable Pre-Pandemic Day'
        ),
        'Access-A-Ride': (
            'Access-A-Ride: Total Scheduled Trips', 
            'Access-A-Ride: % of Comparable Pre-Pandemic Day'
        ),
        'Bridges and Tunnels': (
            'Bridges and Tunnels: Total Traffic', 
            'Bridges and Tunnels: % of Comparable Pre-Pandemic Day'
        ),
        'Staten Island Railway': (
            'Staten Island Railway: Total Estimated Ridership', 
            'Staten Island Railway: % of Comparable Pre-Pandemic Day'
        )
    }

    # 4. 融合 (Melt) 为 Tidy Long Format
    df_tidy_list = []
    for mode, (vol_col, rec_col) in modes_mapping.items():
        if vol_col in df.columns and rec_col in df.columns:
            # 提取该交通方式的特定列
            temp_df = df[['Date', 'Day_of_Week', vol_col, rec_col]].copy()
            # 统一列名为标准名称，供 app.py 调用
            temp_df.columns = ['Date', 'Day_of_Week', 'Ridership_Volume', 'Recovery_Rate']
            # 添加标识该交通方式的维度列
            temp_df['Transit_Mode'] = mode
            df_tidy_list.append(temp_df)

    df_tidy = pd.concat(df_tidy_list, ignore_index=True)

    # 5. 格式化 Date 与星期顺序
    df_tidy['Date'] = df_tidy['Date'].dt.strftime('%Y-%m-%d')
    dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df_tidy['Day_of_Week'] = pd.Categorical(df_tidy['Day_of_Week'], categories=dow_order, ordered=True)
    
    # 按日期排序
    df_tidy = df_tidy.sort_values(by=['Date', 'Transit_Mode'])

    # 6. 导出
    df_tidy.to_csv(output_file, index=False)
    print(f"✅ 数据处理完毕！已成功保存至: {output_file}")
    print(f"总计转换记录数: {len(df_tidy)}")
    print("\n【前 5 行预览】:")
    print(df_tidy.head())

if __name__ == "__main__":
    preprocess_mta_data()