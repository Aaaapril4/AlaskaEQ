import os
import pandas as pd
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import subprocess
import calendar
import numpy as np
from loguru import logger
import multiprocessing as mp
client = Client("IRIS")


workdir = '/mnt/scratch/jieyaqi/alaska'

def Findfile(file):
    result = subprocess.run(f'ls {file}', capture_output=True, shell=True, text=True)
    if not result.stderr:
        return result.stdout.strip()
    else:
        return None



def download_station(id, start):
    net, sta = id.split('.')
    end = start + calendar.monthrange(start.year, start.month)[1] * 60 * 60 * 24
    start = start.strftime('%Y%m%dT000000Z')
    end = end.strftime('%Y%m%dT000000Z')
    channel = {'Z': ['HHZ', 'BHZ', 'EHZ', 'SHZ'], '[1,E]': ['HH1,HHE', 'BH1,BHE', 'EH1,EHE', 'SH1,SHE'], '[2,N]': ['HH2,HHN', 'BH2,BHN', 'EH2,EHN', 'SH2,SHN']}
    for k,v in channel.items():
        name = f'{net}.{sta}.*.??{k}__{start}__{end}.mseed'
        file = Findfile(os.path.join(workdir, 'waveform', sta, name))
        if file != None:
            continue

        for c in v:
            try:
                st = client.get_waveforms(net, sta, "*", c, UTCDateTime(start), UTCDateTime(end))
            except:
                continue
            if len(st) != 0:
                break
        try:
            lst = len(st)
        except:
            # logger.info(
            #     f"No data: {name}")
            continue
        
        if lst == 0:
            # logger.info(
            #     f"No data: {name}")
            continue

        locl = [tr.stats.location for tr in st]
        locl = list(set(locl))
        st = st.select(location = locl[0])
        name = f'{net}.{sta}' + \
                '.' + \
                st[0].stats.location + \
                '.' + \
                st[0].stats.channel + \
                f'__{start}__{end}.mseed'
        logger.info(
                f"Download data [{os.getppid()}]: {name}")
        st.write(os.path.join(workdir, 'waveform', sta, name), format = 'mseed')



if __name__ == '__main__':
    station = pd.read_csv(f'{workdir}/station.txt', delimiter = '|')
    station['id'] = station.apply(lambda x: f'{x["#Network"]}.{x["Station"]}', axis=1)
    start = UTCDateTime(2019, 1, 1)
    end = UTCDateTime(2019, 3, 1)
    
    sta = station['id'].to_numpy()
    startl = []
    i = start
    while i < end:
        startl.append(i)
        i = i + calendar.monthrange(i.year, i.month)[1] * 60 * 60 * 24

    nsta, nt = np.meshgrid(sta, startl)
    nsta = nsta.flatten()
    nt = nt.flatten()

    with mp.Pool(10) as p:
        p.starmap(download_station, zip(nsta, nt))
    # download_station('XO.WD64', UTCDateTime('20190101T000000Z'))
    