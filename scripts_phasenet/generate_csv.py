import pandas as pd
from pathlib import Path
from obspy import UTCDateTime

def generate_csv(datadir: str, stationf: str, outfile: str):
    data = Path(datadir)
    station = pd.read_csv(stationf, delimiter='|')
    staList = list(station.apply(lambda x: f'{x["Network"]}.{x["Station"]}', axis = 1))
    starttime = UTCDateTime("2019-01-01T00:00:00")
    endtime = UTCDateTime("2019-02-28T23:59:59")
    df = pd.DataFrame()

    for sta in staList:
        stalist = sorted(list(data.glob(f'{sta}.*')))
        if len(stalist) == 0:
            continue
        net, st, start, _ = stalist[0].name.split('.')
        cur_start = UTCDateTime(start)
        cur_end = min(cur_start + 10 * 24 * 60 * 60, endtime)

        for mseed in stalist[1:]:
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
    generate_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/data1', '/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', '/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/statime1.csv')