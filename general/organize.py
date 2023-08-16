from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client
import pandas as pd
import calendar
import numpy as np
from loguru import logger
from mpi4py import MPI
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

OUTPUTS = Path(
    "/mnt/scratch/jieyaqi/alaska/waveform")
sq_client = Client("/mnt/scratch/jieyaqi/alaska/phasenet_wins/timeseries.sqlite")

stations = pd.read_csv("/mnt/scratch/jieyaqi/alaska/station_cha.txt", delimiter='|')



def Get_process_list():
    if rank == 0:
        stations['id'] = stations.apply(lambda x: f'{x["Network"]}.{x["Station"]}', axis = 1)
        start = UTCDateTime(2018, 1, 1)
        end = UTCDateTime(2023, 1, 1) - 1e-6

        process_list = []
        idx = 1
        for id in set(stations['id']):
            if not (OUTPUTS / id).exists():
                (OUTPUTS / id).mkdir()
            net, sta = id.split('.')
            channels = stations[stations['id'] == id]['Channel'].to_numpy()
            loc = stations[stations['id'] == id]['Location'].iloc[0]
            if pd.isna(loc):
                loc = ""
            sta_start = UTCDateTime(stations[stations['id'] == id]['StartTime'].iloc[0])
            try:
                sta_end = UTCDateTime(stations[stations['id'] == id]['EndTime'].iloc[0])
            except:
                sta_end = end
            
            current_begin = max(sta_start, start)
            current_begin = UTCDateTime(current_begin.year, current_begin.month, 1)
            while current_begin < min(sta_end, end):
                current_end = current_begin + calendar.monthrange(current_begin.year, current_begin.month)[1] * 60 * 60 * 24 - 1e-6
                for cha in channels:
                    fname = OUTPUTS / f"{net}.{sta}" / f"{net}.{sta}.{loc}.{cha}__{current_begin.strftime('%Y%m%dT%H%M%SZ')}__{current_end.strftime('%Y%m%dT%H%M%SZ')}.mseed"
                    if not fname.exists():
                        process_list.append((idx, net, sta, cha, current_begin, current_end))
                        idx += 1
                current_begin = current_end + 1e-6

        process_every_rank = np.array_split(process_list, size)
        total = len(process_list)
    else:
        total = None
        process_every_rank = None

    process_this_rank = comm.scatter(process_every_rank, root = 0)
    total = comm.bcast(total, root = 0)

    return process_this_rank, total



def Process(process_this_rank, total):
    for id, net, sta, cha, start, end in process_this_rank:
        try:
            st = sq_client.get_waveforms(
                net, sta, "*", cha, start, end)
        except:
            logger.info(
                f"[{rank}]: {id}/{total} !Error accessing data: {net}.{sta} {start}->{end}")
        
        if len(st) != 0:
            fname = OUTPUTS / f"{net}.{sta}" / \
                f"{net}.{sta}.{st[0].stats.location}.{cha}__{start.strftime('%Y%m%dT%H%M%SZ')}__{end.strftime('%Y%m%dT%H%M%SZ')}.mseed"
            st.write(fname, format = 'mseed')
            logger.info(
                f"[{rank}]: {id}/{total} Write {net}.{sta}.{st[0].stats.location}.{cha}__{start.strftime('%Y%m%dT%H%M%SZ')}__{end.strftime('%Y%m%dT%H%M%SZ')}.mseed")



if __name__ == '__main__':
    process_this_rank, total = Get_process_list()
    Process(process_this_rank, total)
