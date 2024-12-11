def parse_sma_csv(file_path: str) -> dict:

    sections = {}
    current_section = None
    current_headers = None
    current_data = []

    with open(file_path, 'r') as f:
        # Skip first line (EOL_Report)
        next(f)

        # Skip initial empty line if present
        line = next(f).strip()
        if not line:
            line = next(f).strip()

        while True:
            try:
                # New section starts with title
                if current_section is None:
                    current_section = line

                    # Skip empty line after title
                    next(f)

                    # Get headers
                    current_headers = next(f).strip().split(',')

                    # Skip empty line after headers
                    next(f)

                    # Start reading data
                    line = next(f).strip()
                    current_data = []
                    continue

                # Empty line marks end of current section
                if not line:
                    # Convert collected data to DataFrame
                    df = pd.DataFrame(current_data, columns=current_headers)

                    # Convert Time column to datetime if it exists
                    if 'Time' in df.columns:
                        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S')

                    sections[current_section] = df
                    current_section = None
                    current_data = []
                    line = next(f).strip()
                    continue

                # Add data row to current section
                current_data.append(line.split(','))
                line = next(f).strip()

            except StopIteration:
                # Convert last section if exists
                if current_section and current_data:
                    df = pd.DataFrame(current_data, columns=current_headers)
                    if 'Time' in df.columns:
                        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S')
                    sections[current_section] = df
                break

        combined_df = None

        for key, df in sections.items():
            if combined_df is None:
                combined_df = df
            else:
                combined_df = pd.merge(combined_df, df, on=["Shot #", "Time"], how="outer")

        # Fill NaN if needed, e.g., with 0 or a placeholder value
        combined_df = combined_df.fillna(0)

    return combined_df

def find_files(start_seq, end_seq, root_dir):

    production_lines = list()
    # Iterate through the range of folder names
    for i in range(start_seq, end_seq):
        folder_name = f'Seq{i}'
        folder_path = os.path.join(root_dir, folder_name)

        if os.path.isdir(folder_path):  # Check if the folder exists
            pp_sp_path = os.path.join(folder_path, 'PP_SP_Range')
            if os.path.isdir(pp_sp_path):
                # print(pp_sp_path)
                for dirpath, dirnames, filenames in os.walk(pp_sp_path):
                    for filename in filenames:
                        if filename.endswith('-SMA_QC.csv'):
                            file_path = os.path.join(dirpath, filename)
                            if file_path[-29] not in ['7']:
                                production_lines.append(file_path)
                                # print(file_path)

    return production_lines


if __name__ == '__main__':


    import pandas as pd
    import os

    # sma_csv = r"Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV\Seq1074\PP_SP_Range\5391121074-SMA_QC.csv"
    # combined_df = parse_sma_csv(sma_csv)
    #
    # print(combined_df.head())

    root_dir = r'Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV'
    start_seq = 1001
    end_seq = 1080

    sma_csv_files = find_files(start_seq, end_seq, root_dir)

    seq_sma_out = list()

    for sma_file in sma_csv_files:
        line_name = sma_file[-21:-11]
        # print(line_name)
        df = parse_sma_csv(sma_file)
        df['V1 SMA m'] = pd.to_numeric(df['V1 SMA m'], errors='coerce')
        ave_sma = df['V1 SMA m'].mean()
        # print(ave_sma)
        if ave_sma > 1:
            seq_sma_out.append((line_name, ave_sma))

    for seq in seq_sma_out:
        print(seq)

    print(len(seq_sma_out))








