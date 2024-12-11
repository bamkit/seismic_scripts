import re
import pandas as pd



def get_4d_preplot_from_file(file_path):
    # Read the file into a pandas DataFrame, assuming each line is a new record
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize an empty list to hold the parsed data
    data_list = []

    # Loop through each line and extract the data using string slicing
    for line in lines:
        # Skip lines that don't start with 'S' (as those are the data lines we care about)
        if not line.startswith('S'):
            continue

        # Preplot line (e.g., 5007)
        preplot_line = line[1:5]

        # Shotpoint (e.g., 5950273017.60N)
        shotpoint = line[21:25].strip()

        # Latitude (degrees, minutes, seconds, N/S)
        lat_deg = int(line[25:27])
        lat_min = int(line[27:29])
        lat_sec = float(line[29:34])
        lat_hemisphere = line[34]

        # Longitude (degrees, minutes, seconds, E/W)
        lon_deg = int(line[35:38])
        lon_min = int(line[38:40])
        lon_sec = float(line[40:45])
        lon_hemisphere = line[45]

        # Easting and Northing
        easting = float(line[47:55].strip())
        northing = float(line[55:64].strip())

        # Convert latitude and longitude to decimal degrees
        latitude = lat_deg + lat_min / 60 + lat_sec / 3600
        longitude = lon_deg + lon_min / 60 + lon_sec / 3600

        # Apply hemisphere adjustments
        if lat_hemisphere == 'S':
            latitude = -latitude
        if lon_hemisphere == 'W':
            longitude = -longitude

        # Append the extracted values to the list
        data_list.append({
            "linename": preplot_line,
            "shotpoint": shotpoint,
            "latitude": latitude,
            "longitude": longitude,
            "easting": easting,
            "northing": northing,
        })

    # Convert the list of data dictionaries to a pandas DataFrame
    df = pd.DataFrame(data_list)
    return df

def get_4d_preplot_endpoints(fourd_preplot_df):
    # Sort the DataFrame by 'preplot_line' and 'shotpoint' for sequential order
    df = fourd_preplot_df.sort_values(by=['linename', 'shotpoint'])

    # Initialize a list to store processed data
    processed_data = []

    # Group by each preplot_line to get the first and last points
    for preplot_line, group in df.groupby('linename'):
        # Get first and last rows of each group
        first = group.iloc[0]
        last = group.iloc[-1]

        # Extract values for first point
        shotpoint1 = first['shotpoint']
        eastings1 = first['easting']
        northings1 = first['northing']
        latitude1 = first['latitude']
        longitude1 = first['longitude']

        # Extract values for last point
        shotpoint2 = last['shotpoint']
        eastings2 = last['easting']
        northings2 = last['northing']
        latitude2 = last['latitude']
        longitude2 = last['longitude']

        # Calculate radial distance (Euclidean distance)
        length = np.sqrt((eastings2 - eastings1)**2 +
                         (northings2 - northings1)**2)

        # Calculate azimuth (angle in degrees from north)
        delta_east = eastings2 - eastings1
        delta_north = northings2 - northings1
        azimuth = np.degrees(np.arctan2(delta_east, delta_north)) % 360

        # Append the processed row to the list
        processed_data.append({
            "linename": preplot_line,
            "sp1": shotpoint1,
            "east1": eastings1,
            "north1": northings1,
            "lat1_deg": latitude1,
            "lon1_deg": longitude1,
            "sp2": shotpoint2,
            "east2": eastings2,
            "north2": northings2,
            "lat2_deg": latitude2,
            "lon2_deg": longitude2,
            "length": length,
            "azimuth": azimuth
        })

    # Create a new DataFrame from the processed data
    result_df = pd.DataFrame(processed_data)
    return result_df

if __name__ == '__main__':

    import numpy as np

    f = r"Y:\NAV\01_Projects\0_KMS_3D_OBN_MT3007424\Preplots\KMS4D2024_NAD27_UTM15N_v2-1_Orca\KMS4D2024_NAD27_UTM15N_v2-1_Orca.190"

    df = get_4d_preplot_from_file(f)

    endpoints_df = get_4d_preplot_endpoints(df)
    print(endpoints_df.head())