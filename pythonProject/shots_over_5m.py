import pandas as pd
import os
from io import StringIO

def find_shots_over_threshold(file_path, threshold=5.0):
    """
    Find shotpoints where A2 SP DDC exceeds the threshold value.
    
    Args:
        file_path (str): Path to the SourceDrift CSV file
        threshold (float): Drift threshold in meters (default 5.0)
        
    Returns:
        DataFrame: Contains rows where drift exceeds threshold
    """
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            # Read the entire file into a list
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
                # print(encoding)
            
            # Find the header line
            header_line = None
            for i, line in enumerate(lines):
                if 'Shot #,Time,A1 SP DDA m,A2 SP DDA m,A3 SP DDA m,A1 SP DDC m,A2 SP DDC m,A3 SP DDC m,A1 SP DDR m,A2 SP DDR m,A3 SP DDR m' in line:
                    header_line = i
                    # print(header_line)
                    break
            
            if header_line is None:
                continue  # Try next encoding if header not found
            
            # Find the first empty line after the header
            end_line = None
            for i in range(header_line + 3, len(lines)):
                if lines[i].strip() == '':
                    end_line = i
                    # print(end_line)
                    break
            
            if end_line is None:
                end_line = len(lines)  # If no empty line found, read to end
            
            # Data starts 2 lines after header and ends at the empty line
            data_start = header_line + 2

            # print(lines[data_start:end_line])
            # Define your custom column names
            columns = ['Shot #', 'Time', 'A1 SP DDA m', 'A2 SP DDA m', 'A3 SP DDA m', 
                       'A1 SP DDC m', 'A2 SP DDC m', 'A3 SP DDC m', 
                       'A1 SP DDR m', 'A2 SP DDR m', 'A3 SP DDR m']
            
            # Read CSV with custom column names
            df = pd.read_csv(StringIO(''.join(lines[data_start:end_line])), 
                            names=columns,    # Use our custom column names
                            header=None)      # Tell pandas there's no header row in the data

            # Create new DataFrame with only Shot # and A2 SP DDC m columns
            df_filtered = df[['Shot #', 'A2 SP DDC m']].dropna()


            # Create new DataFrame with shots where |A2 SP DDC m| > 5
            df_over_5 = df_filtered[abs(df_filtered['A2 SP DDC m']) > threshold]
            print("\nShots with absolute A2 SP DDC m value over 5:")
            # print(df_over_5)

            return df_over_5
                
        except UnicodeDecodeError:
            continue  # Try next encoding if current one fails
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue  # Try next encoding if other errors occur
    
    print(f"Could not read file {file_path} with any supported encoding")
    return pd.DataFrame()

def process_sequence_source_drift(directory_path, sequence_number, threshold=5.0):
    """
    Process SourceDrift CSV files for a specific sequence number.
    
    Args:
        directory_path (str): Path to directory containing SourceDrift files
        sequence_number (str): Four-digit sequence number to process (e.g., '1013')
        threshold (float): Drift threshold in meters (default 5.0)
    """
    
    # Use os.walk to search through all subdirectories
    found_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if f'{sequence_number}-SourceDrift.csv' in file:
                full_path = os.path.join(root, file)
                found_files.append(full_path)
                print(f"Found file: {full_path}")
    
    if not found_files:
        print(f"No SourceDrift CSV files found for sequence {sequence_number}")
        return
    
    # Create a list to store all results
    all_results = []
    
    # Process each file
    for file_path in found_files:
        print(f"\nProcessing sequence {sequence_number} file:", os.path.basename(file_path))
        result = find_shots_over_threshold(file_path, threshold)
        if not result.empty:
            all_results.append(result)
    
    # If we have results, combine them and save to CSV
    if all_results:
        # Combine all results into one DataFrame
        combined_results = pd.concat(all_results, ignore_index=True)
        
        # Sort by Shot number
        combined_results = combined_results.sort_values('Shot #')
        
        # Create output directory if it doesn't exist
        output_dir = r"Y:\NAV\01_Projects\0_KMS_3D_OBN_MT3007424\EOL_Analysis\Source_drifts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        output_file = os.path.join(output_dir, f'{sequence_number}.csv')
        combined_results.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")
        print(f"\nTotal shots over threshold: {len(combined_results)}")
    else:
        print(f"\nNo shots over threshold found for sequence {sequence_number}")

# Example usage:
if __name__ == "__main__":

    import sys

    print("\n\nStarting...")
    directory_path = r"Z:/MT3007424/Murphy_KMS_3D_OBN/00_NAV/"
    sequence_number = sys.argv[1]
    process_sequence_source_drift(directory_path, sequence_number)
    print("\nDone")
    print("\n\n")