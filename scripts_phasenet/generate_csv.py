import pandas as pd
from pathlib import Path
from obspy import UTCDateTime

basedir = '/mnt/scratch/jieyaqi/alaska/phasenet_wins'
data = Path(f"{basedir}/data")
output = Path(basedir)
station = pd.read_csv('/mnt/scratch/jieyaqi/alaska/station.txt', delimiter='|')
staList = list(station.apply(lambda x: f'{x["#Network"]}.{x["Station"]}', axis = 1))
starttime = UTCDateTime("2019-01-01T00:00:00")
endtime = UTCDateTime("2019-03-01T00:00:00")
df = pd.DataFrame()

for sta in staList:
    sta_start = UTCDateTime.now()
    sta_end = UTCDateTime('1970-01-01')
    flag = 0
    for mseed in data.glob(f'{sta}*'):
        flag = 1
        net, sta, start, _ = mseed.name.split('.')
        start = UTCDateTime(start)
        end = min(start + 10 * 24 * 60 * 60, endtime)
        if start < sta_start:
            sta_start = start
        if end > sta_end:
            sta_end = end
    
    if flag != 0:
        statime = pd.Series({
            'network': net,
            'station': sta,
            'start_time': sta_start,
            'end_time': sta_end
        }).to_frame().T
        df = pd.concat([df, statime], ignore_index=True)

outfile = output / 'statime.csv'
df.to_csv(outfile, sep=",", index=False, 
    date_format='%Y-%m-%dT%H:%M:%S.%f')
