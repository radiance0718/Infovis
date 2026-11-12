import os
import pandas as pd

def preprocess_mta_data():
    input_file = "MTA_Daily_Ridership_Data__2020_-_2025_20261013.csv"
    output_file = "mta_tidy_data.csv"

    if not os.path.exists(input_file):
        print(f"Can't find {input_file}")
        return

    df = pd.read_csv(input_file)

    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    df['Day_of_Week'] = df['Date'].dt.strftime('%a')
    
    for col in df.columns:
        if col not in ['Date', 'Day_of_Week']:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

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

    df_tidy_list = []
    for mode, (vol_col, rec_col) in modes_mapping.items():
        if vol_col in df.columns and rec_col in df.columns:
            temp_df = df[['Date', 'Day_of_Week', vol_col, rec_col]].copy()
            temp_df.columns = ['Date', 'Day_of_Week', 'Ridership_Volume', 'Recovery_Rate']
            temp_df['Transit_Mode'] = mode
            df_tidy_list.append(temp_df)

    df_tidy = pd.concat(df_tidy_list, ignore_index=True)

    df_tidy['Date'] = df_tidy['Date'].dt.strftime('%Y-%m-%d')
    dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df_tidy['Day_of_Week'] = pd.Categorical(df_tidy['Day_of_Week'], categories=dow_order, ordered=True)
    
    df_tidy = df_tidy.sort_values(by=['Date', 'Transit_Mode'])

    df_tidy.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")
    print(f"Total records converted: {len(df_tidy)}")
    print("\n[First 5 rows preview]:")
    print(df_tidy.head())

if __name__ == "__main__":
    preprocess_mta_data()