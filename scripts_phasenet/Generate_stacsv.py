from pathlib import Path
import calendar
import pandas as pd
from obspy import UTCDateTime


SEEDS = Path("/mnt/scratch/jieyaqi/alaska/phasenet/test")
process_list = []

data = pd.DataFrame()
for f in sorted(SEEDS.glob("*mseed")):
    net, sta, start = f.name.split('.')[:3]
    starttime = UTCDateTime(start+'-1')
    endtime = starttime + calendar.monthrange(starttime.year, starttime.month)[1] * 60 * 60 * 24
    sta = pd.Series({"network": net, 
                     "station": sta, 
                     "start_time": starttime.strftime('%Y-%m-%dT%H:%M:%S'), 
                     "end_time": endtime.strftime('%Y-%m-%dT%H:%M:%S')}).to_frame().T
    data = pd.concat([data, sta], ignore_index=True)

data.to_csv('phasenet/test.csv', index=False)