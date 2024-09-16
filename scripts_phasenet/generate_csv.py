import pandas as pd
from pathlib import Path
from obspy import UTCDateTime

def generate_csv(datadir: str, stationf: str, outfile: str, starttime: str, endtime:str):
    data = Path(datadir)
    station = pd.read_csv(stationf, delimiter='|')
    staList = list(station.apply(lambda x: f'{x["Network"]}.{x["Station"]}', axis = 1))
    starttime = UTCDateTime(starttime)
    endtime = UTCDateTime(endtime)
    df = pd.DataFrame()

    for sta in staList:
        mseedlist = list(data.glob(f'{sta}.*'))
        mseedlist = sorted(mseedlist, key = lambda x: UTCDateTime(str(x).split('.')[2]))
        if len(mseedlist) == 0:
            continue
        net, st, start, _ = mseedlist[0].name.split('.')
        cur_start = UTCDateTime(start)
        cur_end = min(cur_start + 10 * 24 * 60 * 60, endtime)

        for mseed in mseedlist[1:]:
            net, st, start, _ = mseed.name.split('.')
            start = UTCDateTime(start)
            end = min(start + 10 * 24 * 60 * 60, endtime)

            if start > cur_end + 60 * 60:
                statime = pd.Series({
                    'network': net,
                    'station': st,
                    'start_time': cur_start,
                    'end_time': cur_end
                }).to_frame().T
                df = pd.concat([df, statime], ignore_index=True)

                cur_start = start
                cur_end = end
            else:
                cur_end = end

        statime = pd.Series({
            'network': net,
            'station': st,
            'start_time': cur_start,
            'end_time': cur_end
        }).to_frame().T
        df = pd.concat([df, statime], ignore_index=True)

    df.to_csv(outfile, sep=",", index=False, 
        date_format='%Y-%m-%dT%H:%M:%S.%f')
    return
    
if __name__ == '__main__':
    for i in range(1, 53):
        generate_csv(f'/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/data{i}', '/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', f'/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/statime{i}.csv', '2018-01-01T000000', '2022-12-31T235959')