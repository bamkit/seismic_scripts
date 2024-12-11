def srecords_to_df(srec):

    full_lines = []
    with open(srec, 'r') as f:
        flines = f.readlines()

        for k, v in enumerate(flines):

            if v[0] == 'S':
                entry = list()
                line = v.strip('\n')
                line = line.split(',')
                entry.append(line[0][1:11])
                entry.append(line[0][20:25])
                entry.append(line[0][25:35])
                entry.append(line[0][35:46])
                entry.append(line[0][47:55])
                entry.append(line[0][55:64])
                entry.append('-' + line[0][64:70])
                entry.append(line[0][70:73])
                entry.append(line[0][73:79])

                # z1 = flines[k - 3]
                # zline1 = z1.strip('\n')
                # zline1 = zline1.split(',')
                # entry.append(zline1[0][47:55])
                # entry.append(zline1[0][55:64])
                #
                # z2 = flines[k - 2]
                # zline2 = z2.strip('\n')
                # zline2 = zline2.split(',')
                # entry.append(zline2[0][47:55])
                # entry.append(zline2[0][55:64])
                #
                # z3 = flines[k - 1]
                # zline3 = z3.strip('\n')
                # zline3 = zline3.split(',')
                # entry.append(zline3[0][47:55])
                # entry.append(zline3[0][55:64])

                # for gn positions
                # gn_index = k - 69
                # for i in range(20):
                #     gn_pos = gn_index + i
                #     

                full_lines.append(entry)
                #print(entry)

    def ave_x(x1, x2, x3):
        meanx = (float(x1) + float(x2) + float(x3))/3
        return meanx


    df = pd.DataFrame(data=full_lines, columns=[
                                        'linename',
                                        'sp',
                                        'lat',
                                        'long',
                                        'east',
                                        'north',
                                        'depth',
                                        'jday',
                                        'time',
                                        ]
                      )
    # df['mean e'] = df.apply(lambda x: ave_x(x['ze1'], x['ze2'], x['ze3']), axis=1)
    # df['mean n'] = df.apply(lambda x: ave_x(x['zn1'], x['zn2'], x['zn3']), axis=1)
    #print(df)
    return df

if __name__ == '__main__':

    import pandas as pd
    import os
    from datetime import datetime, timedelta

    boem_file = r"Y:\NAV\01_Projects\0_MT2005724_Engament5_Gain_Test\BOEM\16-31-July-2024\ENG5_16_July_31_July_2024.p190"
    boem_df = srecords_to_df(boem_file)

    jdays = boem_df['jday'].unique()
    #print(jdays)
    jdays_shottime = list()

    for v in jdays:
        #print(v)
        elem = list()
        mask = boem_df['jday'] == v
        masked_df = boem_df[mask]
        linenames = masked_df['linename'].unique()
        #print(linenames)

        day_total = list()
        for line in linenames:

            line_mask = masked_df['linename'] == line
            line_mask_df = masked_df[line_mask]

            t_start = datetime.strptime(line_mask_df['time'].iloc[0], '%H%M%S')
            t_end = datetime.strptime(line_mask_df['time'].tail(1).item(), '%H%M%S')
            tdelta = t_end - t_start
            #print(tdelta)
            day_total.append(tdelta)

        total_duration = sum(day_total, timedelta())
        elem.append(v)
        elem.append(total_duration)
        jdays_shottime.append(elem)
        #print(jdays_shottime)

    shottime_df = pd.DataFrame(data=jdays_shottime, columns=['jday', 'total shot time'])

    print(shottime_df)
    outpath = r"Y:\NAV\01_Projects\01_BOEM\01-15April24"
    # boem_df.to_csv(os.path.join(outpath, 'beom.csv'))

    # print(boem_df.head())