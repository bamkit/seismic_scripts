import sys
import os

scripts_path = r"C:\Users\mta3.sv1.nav\AppData\Local\Programs\Python\Python313\Lib\site-packages"
os.environ["PATH"] += os.pathsep + scripts_path

import pandas as pd
from pyproj import Proj, transform
import math


class PreplotToCsv:

    def __init__(self, preplot_path):
        self.preplot = preplot_path

    # Coverts P190 preplot to a dataframe
    def get_preplot_coordinates(self):

        # preplot = preplot_path
        full_lines = []
        with open(self.preplot, 'r') as f:
            flines = f.readlines()

            for line in flines:

                if line[0] == 'V':
                    line = line.strip('\n')
                    line = line.split()
                    entry = dict()
                    entry['linename'] = line[0][1:]
                    entry['sp'] = line[1][0:5]
                    entry['lat'] = line[1][5:15]
                    entry['lon'] = line[1][15:]
                    entry['east'] = line[2][0:8]
                    entry['north'] = line[2][8:]
                    full_lines.append(entry)
                #print(entry)
# get first SP in else condition and last SP in if condition
        data_dict = {}
        for line in full_lines:
            name = line['linename']

            if name in data_dict: #if line name is in the data_dict,
                data_dict[f'{name}']['sp2'] = line['sp']
                data_dict[f'{name}']['lat2'] = line['lat']
                data_dict[f'{name}']['lon2'] = line['lon']
                data_dict[f'{name}']['east2'] = line['east']
                data_dict[f'{name}']['north2'] = line['north']
            else: #if line name not exists in data_dict, get SP1
                data_dict[f'{name}'] = {}
                data_dict[f'{name}']['sp1'] = line['sp']
                data_dict[f'{name}']['lat1'] = line['lat']
                data_dict[f'{name}']['lon1'] = line['lon']
                data_dict[f'{name}']['east1'] = line['east']
                data_dict[f'{name}']['north1'] = line['north']

        df = pd.DataFrame.from_dict(data=data_dict, orient='index')
        df.reset_index(inplace=True)
        df = df.rename(columns={'index': 'linename'})
        #print(df)

        # function to get preplot length
        def get_dy(north2, north1):
            dy = round(round(float(north2), 3) - round(float(north1), 3), 3)
            return dy

        def get_dx(east2, east1):
            dx = round(round(float(east2), 3) - round(float(east1), 3), 3)
            return dx

        def get_az(dx, dy):
            if dx > 0 and dy > 0:
                az = round(90 - math.degrees(math.atan(dy/dx)), 3)
                return az
            elif dx > 0 and dy < 0:
                dy = abs(dy)
                az = round(90 + math.degrees(math.atan(dy/dx)), 3)
                return az
            elif dx < 0 and dy < 0:
                dx = abs(dx)
                dy = abs(dy)
                az = round(270 + math.degrees(math.atan(dy/dx)), 3)
                return az
            elif dx < 0 and dy > 0:
                dx = abs(dx)
                az = round(270 + math.degrees(math.atan(dy/dx)), 3)
                return az
            elif dx == 0 and dy > 0:
                return 0.0
            elif dx == 0 and dy < 0:
                return 180.0
            elif dx > 0 and dy == 0:
                return 90.0
            elif dx < 0 and dy == 0:
                return 270.0
            
        def get_distance(dE, dN):
            d = (dE**2 + dN**2)**0.5
            return d

        df['dE'] = df.apply(lambda x: get_dx(x['east2'], x['east1']), axis=1)
        df['dN'] = df.apply(lambda x: get_dy(x['north2'], x['north1']), axis=1)
        df['Az'] = df.apply(lambda x: get_az(x['dE'], x['dN']), axis=1)
        df['length'] = df.apply(lambda x: get_distance(x['dE'], x['dN']), axis=1)

        return df

    # returns dataframe of start and end points
    def create_points(self):

        df = self.get_preplot_coordinates()
        startpoint_df = df[['linename', 'sp1', 'east1', 'north1']].copy()
        endpoint_df = df[['linename', 'sp2', 'east2', 'north2']].copy()

        return startpoint_df, endpoint_df

    # returns a dictionary of preplot lines dataframes
    def get_preplot_shots(self):

        spi = 16.666666666667

        df = self.get_preplot_coordinates()
        numrows = len(df.index)

        def grid_to_geographic(easting, northing):

            # Define UTM projection
            utm_proj = Proj(proj="utm", zone=15, datum="WGS84", ellps="WGS84")
            # Define WGS 84 projection
            wgs84_proj = Proj(proj="latlong", datum="WGS84", ellps="WGS84")

            longitude, latitude = transform(utm_proj, wgs84_proj, easting, northing)
            return latitude, longitude

        df_dict = {}
        for k, v in df['linename'].items():

            d0 = int(df.at[k, 'length'])
            e0 = float(df.at[k, 'east1'])
            n0 = float(df.at[k, 'north1'])
            sp0 = int(df.at[k, 'sp1'])
            a = float(df.at[k, 'Az'])

            segments = round(d0/spi)
            data_list = []

            for i in range(segments+1):
                d = spi*i
                e = e0 + d * math.sin(math.radians(a))
                n = n0 + d * math.cos(math.radians(a))
                sp = sp0 + i
                lat, lon = grid_to_geographic(e, n)
                point = [sp, e, n, lat, lon]
                data_list.append(point)

            df_dict[f'{v}'] = pd.DataFrame(data=data_list, columns=['sp', 'east', 'north', 'lat', 'lon'])
        return df_dict


if __name__ == '__main__':
    import pandas as pd
    import os
    import math

    preplot_fullpath = r"Y:\NAV\01_Projects\0_MT2005724_Engament5_Gain_Test\Preplots\Engagement5_20240705_SRC_WGS84_UTM15N_Orca.p190"
    points_csv = r"Y:\NAV\01_Projects\0_MT2005724_Engament5_Gain_Test\QGIS\Preplots"
    startpoints_file = 'startpoint.csv'
    endpoint_file = 'endpoint.csv'
    # shotpoint_file = 'allshots.csv'

    preplot = PreplotToCsv(preplot_fullpath)
    df = preplot.get_preplot_coordinates()
    linename_dict = preplot.get_preplot_shots()

    for line, df in linename_dict.items():
        df.to_csv(os.path.join(points_csv, line + '.csv'))
