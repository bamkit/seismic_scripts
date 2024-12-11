import os


os.environ['TCL_LIBRARY'] = r'C:\Users\mta3.sv1.nav\AppData\Local\Programs\Python\Python312\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\mta3.sv1.nav\AppData\Local\Programs\Python\Python312\tcl\tk8.6'
import tkinter

def datestdtojd(col):

    sdtdate = col.timetuple()
    jdate = sdtdate.tm_yday
    return jdate

def convert_to_knots(spd):
    return spd*1.94384

def time_to_datetime(col):
    return datetime.strptime(col, '%d/%m/%Y %H:%M:%S')


def eolreport_to_df(f):
    df = pd.read_csv(f, sep=',', skiprows=[0, 1, 2, 3, 5], encoding='ISO-8859-1')
    # print(df.columns)
    return df


# Input df from eol report
def create_time_series(df_all_columns, linename, png_dir):

    output_file = os.path.join(png_dir, linename + '-bsp_wsp.png')

    df = df_all_columns[['Shot #', 'Time', 'V1GY4 Obs °', 'V1E1 Obs m', 'V1WS1 Calc', 'V1 BSP m/s']].copy()
    print(df.head())
    df.loc[:, 'BSP knots'] = df['V1 BSP m/s'] * 1.94384
    df.loc[:, 'WSP knots'] = df['V1WS1 Calc'] * 1.94384

    plt.figure(figsize=(20, 12))

    plt.plot(df['Shot #'], df['BSP knots'], label='BSP in knots', marker='d')
    plt.plot(df['Shot #'], df['WSP knots'], label='WSP in knots', marker='.')

    # Calculate and plot the average lines
    avg_bsp = df['BSP knots'].mean()


    avg_wsp = df['WSP knots'].mean()
    avg_hdg = df['V1GY4 Obs °'].mean()

    if avg_hdg > 180:
        line_dir = '270°'
    else:
        line_dir = '90°'

    plt.axhline(y=avg_bsp, color='blue', linestyle='--', linewidth=1, label=f'Avg BSP: {avg_bsp:.2f}')
    plt.axhline(y=avg_wsp, color='orange', linestyle='--', linewidth=1, label=f'Avg WSP: {avg_wsp:.2f}')

    # Adding title and labels
    plt.title(f'Line {linename} BSP vs WSP. LINE DIRECTION is {line_dir}')
    plt.xlabel('Shot')
    plt.ylabel('Knots')

    # Adding legend
    plt.legend()

    # Display the plot
    plt.savefig(output_file)


def create_excel_files(df_all_columns, linename, png_dir):
    # Define output files
    excel_file = os.path.join(png_dir, r'Excel_files\\' + linename + '-bsp_wsp.xlsx')
    png_file = os.path.join(png_dir, r'Png_files\\' + linename + '-bsp_wsp.png')

    # Filter and compute new columns
    df = df_all_columns[['Shot #', 'Time', 'V1GY4 Obs °', 'V1E1 Obs m', 'V1WS1 Calc', 'V1 BSP m/s']].copy()

    df.loc[:, 'BSP knots'] = df['V1 BSP m/s'] * 1.94384
    df.loc[:, 'WSP knots'] = df['V1WS1 Calc'] * 1.94384

    # # Plotting the BSP and WSP time series with matplotlib and save as PNG
    plt.figure(figsize=(12, 6))
    plt.plot(df['Shot #'], df['BSP knots'], label='BSP in knots', marker='d')
    plt.plot(df['Shot #'], df['WSP knots'], label='WSP in knots', marker='.')

    avg_bsp = df['BSP knots'].mean()
    avg_wsp = df['WSP knots'].mean()
    avg_hdg = df['V1GY4 Obs °'].mean()

    # Determine line direction
    line_dir = '180°' if 90 < avg_hdg < 270 else '0°'

    # Plot average lines
    plt.axhline(y=avg_bsp, color='blue', linestyle='--', linewidth=1, label=f'Avg BSP: {avg_bsp:.2f}')
    plt.axhline(y=avg_wsp, color='orange', linestyle='--', linewidth=1, label=f'Avg WSP: {avg_wsp:.2f}')

    # Add title and labels
    plt.title(f'Line {linename} BSP vs WSP. LINE DIRECTION is {line_dir}')
    plt.xlabel('Shot')
    plt.ylabel('Knots')
    plt.legend()

    # Save plot to PNG file
    plt.savefig(png_file)
    plt.close()

    # Create Excel file with data and chart
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        # Write data to 'Data' sheet
        df.to_excel(writer, sheet_name='Data', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Data']

        # Create average columns
        df['Avg BSP'] = avg_bsp
        df['Avg WSP'] = avg_wsp

        # Insert PNG plot into the Excel file in a new sheet
        chart_worksheet = workbook.add_worksheet('Plot')
        # with open(png_file, 'rb') as img_file:
        chart_worksheet.insert_image('B2', png_file)

        # Create an Excel chart in a new sheet
        chart_worksheet = workbook.add_worksheet('Chart')
        chart = workbook.add_chart({'type': 'line'})

        # Add series for BSP knots
        chart.add_series({
            'name': 'BSP in knots',
            'categories': ['Data', 1, 0, len(df), 0],  # 'Shot #' is in column A
            'values': ['Data', 1, 6, len(df), 6],  # 'BSP knots' is in column G
            'line': {'color': 'blue'},
            'marker': {'type': 'diamond'}
        })

        # Add series for WSP knots
        chart.add_series({
            'name': 'WSP in knots',
            'categories': ['Data', 1, 0, len(df), 0],  # 'Shot #' is in column A
            'values': ['Data', 1, 7, len(df), 7],  # 'WSP knots' is in column H
            'line': {'color': 'orange'},
            'marker': {'type': 'circle'}
        })

        # Then, add series for average values using correct parameters:
        chart.add_series({
            'name': f'Avg BSP: {avg_bsp:.2f}',
            'categories': ['Data', 1, 0, len(df), 0],
            'values': ['Data', 1, len(df.columns) - 2, len(df), len(df.columns) - 2],  # Column for Avg BSP
            'line': {'color': 'blue', 'dash_type': 'dash'}
        })

        chart.add_series({
            'name': f'Avg WSP: {avg_wsp:.2f}',
            'categories': ['Data', 1, 0, len(df), 0],
            'values': ['Data', 1, len(df.columns) - 1, len(df), len(df.columns) - 1],  # Column for Avg WSP
            'line': {'color': 'orange', 'dash_type': 'dash'}
        })

        # Configure the chart axes and title
        chart.set_title({'name': f'Line {linename} BSP vs WSP'})
        chart.set_x_axis({'name': 'Shot'})
        chart.set_y_axis({'name': 'Knots'})

        # Insert the chart into the Excel file
        chart_worksheet.insert_chart('B2', chart)


if __name__ == '__main__':

    import pandas as pd
    from datetime import datetime
    import matplotlib.pyplot as plt
    import os
    import numpy as np
    from io import BytesIO

    # ... existing code ...
    os.environ['TCL_LIBRARY'] = r'C:\Users\mta3.sv1.nav\AppData\Local\Programs\Python\Python313\tcl\tcl8.6'
    os.environ['TK_LIBRARY'] = r'C:\Users\mta3.sv1.nav\AppData\Local\Programs\Python\Python313\tcl\tk8.6'
    # ... existing code ...

    # p111_file = r"Z:\PROJECT_DATA\07_P111\2404115369.WGS84.p111"

    # eol_report = r"Z:\PROJECT_DATA\00_NAV\Seq5369\PP_SP_Range\2404115369-AAT_Shot_Table.csv"

    png_dir = r'Y:\NAV\01_Projects\0_KMS_3D_OBN_MT3007424\BSP_WSP_Comparisons'

    root_dir = r'Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV'

    production_lines = list()
    # Iterate through the range of folder names
    for i in range(1060, 1135):  # 5370 is used because the range is exclusive at the end
        folder_name = f'Seq{i}'
        folder_path = os.path.join(root_dir, folder_name)

        if os.path.isdir(folder_path):  # Check if the folder exists
            pp_sp_path = os.path.join(folder_path, 'PP_SP_Range')
            if os.path.isdir(pp_sp_path):
                # print(pp_sp_path)
                for dirpath, dirnames, filenames in os.walk(pp_sp_path):
                    for filename in filenames:
                        if filename.endswith('AAT_Shot_Table.csv'):
                            file_path = os.path.join(dirpath, filename)
                            if file_path[-29] not in ['7']:
                                production_lines.append(file_path)
                                print(file_path)

    # UNCOMMENT IF YOU WANT TO MAKE NEW GRAPHS
    for eol_csv in production_lines:
        line_name = eol_csv[-29:-19]

        # print(output_file)
        df_all = eolreport_to_df(eol_csv)
        # create_time_series(df_all, line_name)
        create_excel_files(df_all, line_name, png_dir)

    # # CREATE A DATAFRAME FOR ALL THE PRODUCTION LINE
    #
    # list_of_df = []
    #
    # for eol_csv in production_lines:
    #
    #     line_df = eolreport_to_df(eol_csv)
    #     list_of_df.append(line_df)
    #
    # main_df = pd.concat(list_of_df, ignore_index=True)
    # trimmed_df = main_df[['Shot #', 'Time', 'V2GY4 Obs °', 'V2E1 Obs m']]
    # trimmed_df['BSP knots'] = main_df['V2 BSP m/s'].apply(convert_to_knots)
    # trimmed_df['WSP knots'] = main_df['V2WS1 Calc'].apply(convert_to_knots)
    # trimmed_df['Datetime'] = trimmed_df['Time'].apply(time_to_datetime)
    # trimmed_df['Day'] = trimmed_df['Datetime'].dt.day
    # trimmed_df['month'] = trimmed_df['Datetime'].dt.strftime('%Y-%m')
    #
    # # print(trimmed_df.head())
    #
    # # Group by month and day, then calculate the average speeds
    # average_speeds_per_day = trimmed_df.groupby(['month', 'Day'])[['WSP knots', 'BSP knots']].mean().reset_index()
    #
    # # Plot the bar graphs for each month
    # months = average_speeds_per_day['month'].unique()
    #
    # for month in months:
    #     month_data = average_speeds_per_day[average_speeds_per_day['month'] == month]
    #
    #     plt.figure(figsize=(12, 6))
    #
    #     bar_width = 0.4
    #     x = np.arange(len(month_data['Day']))
    #
    #     plt.bar(x - bar_width / 2, month_data['WSP knots'], width=bar_width, label='Water Speed', color='skyblue')
    #     plt.bar(x + bar_width / 2, month_data['BSP knots'], width=bar_width, label='Bottom Speed', color='orange')
    #
    #     # Add title and labels
    #     plt.title(f'Average Speed Per Day - {month}')
    #     plt.xlabel('Day of the Month')
    #     plt.ylabel('Average Speed')
    #
    #     # Add x-axis labels
    #     plt.xticks(x, month_data['Day'])
    #
    #     # Add legend
    #     plt.legend()
    #
    #     # Show the plot
    #     plt.show()