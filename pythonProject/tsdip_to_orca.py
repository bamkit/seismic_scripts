# reads the tsdip from the node boats
def parse_tsdip(tsdip):

    df = pd.read_csv(tsdip, sep='\t', skiprows=27)
    df = df.drop(columns=['Unnamed: 8'])
    return df


def tsdip_to_svp_format(df):

    svp_df = df[['PRESSURE;DBAR', 'Calc. SOUND VELOCITY;M/SEC', 'TEMPERATURE;C', 'Calc. SALINITY;']].copy()

    return svp_df


if __name__ == '__main__':
    import pandas as pd
    from datetime import datetime
    import os
    import sys

    tsdipfile = sys.argv[1]

    tsdip_header = [
        'Latitude	"xx,xx,xxN"\n',
        'Longitude	"xx,xx,xxW"\n',
        'Date	xx/xx/2024\n',
        'Time	xx\n',
        'Description	Valeport SVX2 #40710\t\t\n'
        ]

    tsdip_out = r"Y:\NAV\TSDip\SVP\Tsdip_from_script"
    current_datetime = datetime.now().strftime("%Y-%m-%d")
    svp_name = os.path.join(tsdip_out, 'tdsip_' + current_datetime + '.svp')
    orca_format = os.path.join(tsdip_out, 'orcatsdip_' + current_datetime + '.svp')

    tsdip_df = parse_tsdip(tsdipfile)
    orca_tsdip = tsdip_to_svp_format(tsdip_df)
    orca_tsdip.to_csv(svp_name, sep='\t', index=False, header=None)

    with open(svp_name, 'r') as f:
        f_readlines = f.readlines()
        # print(tsdip_header)
        orca_tsdip = tsdip_header + f_readlines

    with open(orca_format, 'w') as f:
        f.writelines(orca_tsdip)

    os.remove(svp_name)
