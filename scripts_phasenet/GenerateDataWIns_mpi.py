import pandas as pd
import h5py
import warnings
from loguru import logger
from pathlib import Path
import numpy as np
import obspy
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy.taup import TauPyModel
model = TauPyModel(model="PREM")
from mpi4py import MPI
import os

warnings.filterwarnings("ignore")

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/timeseries.sqlite")
station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events/events.csv')
picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manualPicks.csv')

def CalSNR(data, phase_index, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(np.abs(tr[0:window*40]), 95) + 1e-6
        s = np.percentile(np.abs(tr[max(phase_index): max(phase_index) + window*40]), 95) + 1e-6
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def Process_kernel(evid, sta, starttime, endtime, idx, total):
    
    evdf = event[event['evid'] == evid]

    picksev = picks[picks["evid"] == evid]
    picksevsta = picksev[picksev['station'] == sta]
    picksevsta['timestamp'] = picksevsta['timestamp'].apply(lambda x: UTCDateTime(x))
    picksevsta = picksevsta.sort_values('timestamp')

    id = picksevsta.iloc[0]['id']
    picksevsta[picksevsta['timestamp'] >= starttime]
    picksevsta[picksevsta['timestamp'] <= endtime]

    try:
        st = sq_client.get_waveforms(
            "*", sta, "*", "*", starttime - 60, endtime + 60
        )
    except:
        logger.info(
            f"!Error accessing data: {sta} {starttime}->{endtime}"
        )
        return None, None, None

    if len(st) == 0:
        logger.info(
            f"!Error accessing data: {sta} {starttime}->{endtime}")
        return None, None, None

    channels = []
    for tr in st:
        channels.append(tr.stats.channel[2])
    channels = set(channels)

    if ('Z' not in channels) or (('E' not in channels) and ('1' not in channels)) or (('N' not in channels) and ('2' not in channels)):
        logger.info(
            f"!Only 1 channel: {sta} {starttime}->{endtime}")
        return None, None, None
    
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")
        
    try:
        st.interpolate(sampling_rate=40)
    except ValueError:
        for tr in st:
            try:
                tr.interpolate(sampling_rate=40)
            except ValueError:
                st.remove(tr)
        
    st.merge(method=1, fill_value="latest")

    if len(st) == 0:
        logger.info(
                f"!Error processing data: {sta} {starttime}->{endtime}")
        return None, None, None

    masks = []
    st.sort()
    for i in range(len(st)):
        if type(st[i].data) == np.ma.MaskedArray:
            masks.append(st[i].data.mask)
        else:
            masks.append(np.zeros(len(st[i].data), dtype=bool))

    for i in range(len(st)):
        st[i].data[masks[i]] = 0
        
    st.trim(starttime, endtime)

    if st == None or len(st) == 0 or len(st[0].data) < (endtime-starttime) * 40:
        logger.info(
            f"!Error data length: {sta} {starttime}->{endtime}")
        return None, None, None
    
    st.sort()
    try:
        stadata = np.stack([tr.data for tr in st])[:, :24000] # stack in 1/E, 2/N, Z order
    except ValueError:
        logger.info(
            f"!Error data length: {sta} {starttime}->{endtime}")
        return None, None, None
    phase_index = ((picksevsta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)

    stainfo = station[station['id'] == id]
    dist, backazimuth, azimuth = obspy.geodetics.base.gps2dist_azimuth(stainfo.iloc[0]['latitude'], stainfo.iloc[0]['longitude'], evdf.iloc[0]['latitude'], evdf.iloc[0]['longitude'])
    
    stameta = {
        'azimuth': round(azimuth, 4), 
        'back_azimuth': round(backazimuth, 4), 
        'begin_time': str(starttime), 
        'component': [tr.stats.channel[2] for tr in st], 
        'distance_km':round(dist/1000, 4), 
        'dt_s': st[0].stats.delta, 
        'elevation_m': stainfo.iloc[0]['elevation(m)'], 
        'end_time': str(endtime), 
        'event_id': evid, 
        'latitude': stainfo.iloc[0]['latitude'], 
        'local_depth_m': 0.0, 
        'location': st[0].stats.location, 
        'longitude': stainfo.iloc[0]['longitude'], 
        'network': st[0].stats.network, 
        'phase_index': phase_index, 
        'phase_polarity': [''] * len(picksevsta), 
        'phase_score': [1] * len(picksevsta), 
        'phase_time': [str(x) for x in picksevsta['timestamp']], 
        'phase_type': [str(x) for x in picksevsta['type']], 
        'snr': CalSNR(np.array(stadata), phase_index, 10), 
        'station': st[0].stats.station, 
        'takeoff_angle': -1, 
        'unit': 'm/s'}

    phase = pd.DataFrame({
        'event_id': [evid] * len(picksevsta),
        'station_id': [st[0].stats.station] * len(picksevsta),
        'phase_index': phase_index,
        'phase_time': [str(x) for x in picksevsta['timestamp']],
        'phase_score': [1] * len(picksevsta),
        'phase_type': [str(x) for x in picksevsta['type']],
        'phase_polarity': [''] * len(picksevsta)
    })
    
    logger.info(
            f"[{rank}] {idx}/{total} Processed {evid}-{sta}"
        )
    
    return stadata, stameta, phase



def Get_list_this_rank(event, picks):
    if rank == 0:
        idx = 1
        process_list = []
        # for evid in set(event.evid):
        for evid in ['123']:
        # for evid in ['01862e2n88']:
            picksev = picks[picks["evid"] == evid]
            for sta in set(picksev.station):
                picksevsta = picksev[picksev['station'] == sta]
                picksevsta['timestamp'] = picksevsta['timestamp'].apply(lambda x: UTCDateTime(x))
                phasep = picksevsta[picksevsta['type']=='P']
                if len(phasep) == 0:
                    continue
                else:
                    starttime = phasep.iloc[0]['timestamp'] - 5*60
                    endtime = starttime + 10*60
                process_list.append((evid, sta, starttime, endtime, idx))
                idx += 1
        process_every_rank = np.array_split(process_list, size)
        total = len(process_list)
    else:
        total = None
        process_every_rank = None
    
    process_this_rank = comm.scatter(process_every_rank, root = 0)
    total = comm.bcast(total, root = 0)
    return process_this_rank, total



def Process(process_this_rank, total):
    phases = pd.DataFrame()
    processeddata = {}
    for evid, sta, starttime, endtime, idx in process_this_rank:
        stadata, stameta, phase = Process_kernel(evid, sta, starttime, endtime, idx, total)
        if stameta != None:
            processeddata[f'{evid}_{sta}'] = {'data': stadata, 'meta': stameta}
            phases = pd.concat([phases, phase], ignore_index=True)
    return processeddata, phases



if __name__ == '__main__':
    process_this_rank, total = Get_list_this_rank(event, picks)
    processeddata, phases = Process(process_this_rank, total)
    
    # collect all data
    phases = comm.gather(phases, root = 0)
    # comm.Gatherv(processeddata, [recvbuf, total], root=0)
    processeddata = comm.gather(processeddata, root = 0)

    # write in h5py file
    if rank == 0:
        processed_data_all = {}
        for data in processeddata:
            processed_data_all.update(data)
        
        phases_all = pd.DataFrame()
        for phase in phases:
            phases_all = pd.concat([phases_all, phase], ignore_index = True)

        logger.info(
            "Start writing files")

        stead = h5py.File(f'/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/Alaska.hdf5', 'a')
        catalogs = pd.DataFrame()

        for evsta, phasedata in processed_data_all.items():
            evid, sta = evsta.split('_')

            # if event not in dataset, add dataset and metadata
            if f"/{evid}" not in stead:
                evdf = event[event['evid'] == evid]
                evmeta = {
                    'begin_time': '', 
                    'depth_km': evdf.iloc[0]['depth'], 
                    'end_time': '', 
                    'event_id': evid, 
                    'event_time': evdf.iloc[0]['time'], 
                    'event_time_index': -1, 
                    'latitude': evdf.iloc[0]['latitude'], 
                    'longitude': evdf.iloc[0]['longitude'], 
                    'magnitude': evdf.iloc[0]['magnitude'], 
                    'magnitude_type': 'mb', 
                    'source': 'ACE'
                    }

                evdata = stead.create_group(evid)
                for k, v in evmeta.items():
                    evdata.attrs[k] = v
                catalog = pd.Series(evmeta).to_frame().T
                catalogs = pd.concat([catalogs, catalog], ignore_index=True)
            
            # add phase data and meta
            stadata = evdata.create_dataset(f"/{evid}/{sta}", data = phasedata['data'])
            for k, v in phasedata['meta'].items():
                stadata.attrs[k] = v

        catalogf = '/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/catalogs.csv'
        if os.path.exists(catalogf):
            catalog = pd.read_csv(catalogf)
            catalogs = pd.concat([catalogs, catalog], ignore_index=True)
            catalogs.to_csv(catalogf, sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        else:
            catalogs.to_csv(catalogf, sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        
        phasef = '/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/phases.csv'
        if os.path.exists(phasef):
            phase = pd.read_csv(phasef)
            phases_all = pd.concat([phases_all, phase], ignore_index=True)
            phases_all.to_csv(catalogf, sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        else:
            phases_all.to_csv(catalogf, sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')