import pandas as pd
import h5py
from loguru import logger
from pathlib import Path
from itertools import repeat
import numpy as np
import multiprocessing as mp
import obspy
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy.taup import TauPyModel
model = TauPyModel(model="PREM")

XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/timeseries.sqlite")


def CalSNR(data, phase_index, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(np.abs(tr[0:window*40]), 95) + 1e-6
        s = np.percentile(np.abs(tr[max(phase_index): max(phase_index) + window*40]), 95) + 1e-6
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def ProcessData(index, processList, lock, phases, processeddata):
    [evid, sta, starttime, endtime, idx] = processList[processList[:,4] == index][0]
    
    evdf = event[event['evid'] == evid]

    picksev = picks[picks["evid"] == evid]
    picksevsta = picksev[picksev['station'] == sta]
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
        return

    if len(st) == 0:
        logger.info(
            f"!Error accessing data: {sta} {starttime}->{endtime}")
        return

    channels = []
    for tr in st:
        channels.append(tr.stats.channel[2])
    channels = set(channels)

    if ('Z' not in channels) or (('E' not in channels) and ('1' not in channels)) or (('N' not in channels) and ('2' not in channels)):
        logger.info(
            f"!Only 1 channel: {sta} {starttime}->{endtime}")
        return
    
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
        return

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
        return      
    
    st.sort()
    try:
        stadata = np.stack([tr.data for tr in st])[:, :24000] # stack in 1/E, 2/N, Z order
    except ValueError:
        logger.info(
            f"!Error data length: {sta} {starttime}->{endtime}")
        return
    
    # double check stadata
    if np.any(np.isnan(stadata)):
        stadata = np.nan_to_num(stadata, 0)
    if stadata.shape[0] != 3:
        return
    
    phase_index = ((picksevsta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)

    stainfo = station[station['id'] == id]
    dist, backazimuth, azimuth = obspy.geodetics.base.gps2dist_azimuth(stainfo.iloc[0]['latitude'], stainfo.iloc[0]['longitude'], evdf.iloc[0]['latitude'], evdf.iloc[0]['longitude'])
    
    stameta = {
        'azimuth': round(azimuth, 4), 
        'back_azimuth': round(backazimuth, 4), 
        'begin_time': str(starttime), 
        'component': [tr.stats.channel[2] for tr in st], 
        'distance_km': round(dist/1000, 4), 
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
    with lock:
        processeddata[f'{evid}_{sta}'] = {'data': stadata, 'meta': stameta}
        phases.df = pd.concat([phases.df, phase], ignore_index=True)
    
    logger.info(
            f"{idx}/{len(processList)} Processed {evid}-{sta}"
        )

    return



def GetTraceList(event, picks):
    processList = []
    idx = 0
        
    # for evid in ['0186sw0feb']:
    for evid in set(event.evid):
        picksev = picks[picks["evid"] == evid]
        for sta in set(picksev.station):
            picksevsta = picksev[picksev['station'] == sta]
            phasep = picksevsta[picksevsta['type']=='P']
            if len(phasep) == 0:
                continue
            else:
                starttime = phasep.iloc[0]['timestamp'] - 5*60
                endtime = starttime + 10*60
            processList.append([evid, sta, starttime, endtime, idx])
            idx += 1
    
    return np.array(processList)



if __name__ == '__main__':
    station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
    event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv', delimiter = '\t')
    picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manualPicks.csv')
    picks['timestamp'] = picks['timestamp'].apply(lambda x: UTCDateTime(x))
    datadir = '/mnt/scratch/jieyaqi/alaska/waveform'
    stead = h5py.File('/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/Alaska.hdf5', 'w')
    catalogs = pd.DataFrame()
    phases = pd.DataFrame()

    processList = GetTraceList(event, picks)
    manager = mp.Manager()
    lock = manager.Lock()
    phases = manager.Namespace()
    phases.df = pd.DataFrame()
    
    pool_num = 10
    pool_size = len(processList) // pool_num + bool(len(processList) % pool_num)
    i = 0
    while i < pool_num:
        processeddata = manager.dict()
        tempindex = range(pool_size * i, min(pool_size * (i + 1), len(processList)))
        with mp.Pool(40) as p:
            results = p.starmap(ProcessData,
                                zip(
                                    tempindex,
                                    repeat(processList),
                                    repeat(lock),
                                    repeat(phases),
                                    repeat(processeddata)
                                ))
        i += 1

        for evsta, phasedata in dict(processeddata).items():
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
            if phasedata['data'].shape[0] == 3:
                stadata = evdata.create_dataset(f"/{evid}/{sta}", data = phasedata['data'])
                for k, v in phasedata['meta'].items():
                    stadata.attrs[k] = v

    with open('/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/catalogs.csv', 'w') as fp:
        catalogs.to_csv(fp, sep=",", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')
    
    with open('/mnt/scratch/jieyaqi/alaska/phasenet_wins/dataset/phases.csv', 'w') as fp:
        phases.df.to_csv(fp, sep=",", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')