import pandas as pd
import h5py
from loguru import logger
import numpy as np
from mpi4py import MPI
import obspy
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client as sql_client
import warnings

warnings.filterwarnings("ignore")

sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/data.sqlite")
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

def CalSNR(data, phase_index, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(np.abs(tr[0:window*40]), 95) + 1e-6
        s = np.percentile(np.abs(tr[max(phase_index): max(phase_index) + window*40]), 95) + 1e-6
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def ProcessData(process_index_this_rank, processList, event, picks, station):
    processeddata = {}
    phases = pd.DataFrame()
    for index in process_index_this_rank:
        [evid, net, sta, starttime, endtime, idx] = processList[processList[:,5] == index][0]
        evdf = event[event['event_index'] == evid]
        picksev = picks[picks["event_index"] == evid]
        id = f'{net}.{sta}..BH'

        picksevsta = picksev[picksev['id'] == id]
        picksevsta = picksevsta.sort_values('timestamp')
        picksevsta[picksevsta['timestamp'] >= starttime]
        picksevsta[picksevsta['timestamp'] <= endtime]

        try:
            st = sq_client.get_waveforms_bulk(
                [("*", sta, "*", "*", starttime - 60, endtime + 60)], None
            )
        except:
            logger.info(
                f"!Error accessing data: {evid}-{id} {starttime}->{endtime}"
            )
            continue

        ### Process data
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

        masks = []
        for i in range(len(st)):
            if type(st[i].data) == np.ma.MaskedArray:
                masks.append(st[i].data.mask)
            else:
                masks.append(np.zeros(len(st[i].data), dtype=bool))

        for i in range(len(st)):
            st[i].data[masks[i]] = 0
            
        st.trim(starttime, endtime, pad=True, fill_value=0)

        if st == None or len(st) == 0:
            logger.info(
                f"!Error accessing data: {evid}-{id} {starttime}->{endtime}")
            continue     
    
        ### Padding data
        channels = []
        padding = []
        for tr in st:
            channels.append(tr.stats.channel[2])

        if 'Z' not in channels:
            trz = st[0].copy()
            trz.data = np.zeros(len(trz.data))
            trz.stats.channel = st[0].stats.channel[:2]+'Z'
            st.append(trz)
            padding.append('Z')

        if 'E' not in channels and '1' not in channels:
            tre = st[0].copy()
            tre.data = np.zeros(len(tre.data))
            tre.stats.channel = st[0].stats.channel[:2]+'E'
            st.append(tre)
            padding.append('E')

        if 'N' not in channels and '2' not in channels:
            trn = st[0].copy()
            trn.data = np.zeros(len(trn.data))
            trn.stats.channel = st[0].stats.channel[:2]+'N'
            st.append(trn)
            padding.append('N')

        st.sort()
    
        channels = [''] * len(st)
        for i in range(len(st)):
            cha = st[i].stats.channel[2]
            if cha in padding:
                channels[i] = ''
            else:
                channels[i] = cha
        
        try:
            stadata = np.stack([tr.data for tr in st])[:, :24000] # stack in 1/E, 2/N, Z order
        except ValueError:
            logger.info(
                f"!Error data length: {evid} {sta} {starttime}->{endtime}")
            continue
    
        if stadata.shape[0] != 3:
            logger.info(
                f"!Error data shape: {evid} {sta} {starttime}->{endtime}")
            continue
    
        # double check nan in stadata
        if np.any(np.isnan(stadata)):
            stadata = np.nan_to_num(stadata, 0)
    
        phase_index = ((picksevsta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)

        stainfo = station[station['id'] == id]
        dist, backazimuth, azimuth = obspy.geodetics.base.gps2dist_azimuth(stainfo.iloc[0]['latitude'], stainfo.iloc[0]['longitude'], evdf.iloc[0]['latitude'], evdf.iloc[0]['longitude'])
    
        stameta = {
            'azimuth': round(azimuth, 4), 
            'back_azimuth': round(backazimuth, 4), 
            'begin_time': str(starttime), 
            'component': channels, 
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

        processeddata[f'{evid}_{id}'] = {'data': stadata, 'meta': stameta}
        phases = pd.concat([phases, phase], ignore_index=True)
    
        logger.info(
                f"{rank}: {idx}/{len(processList)} Processed {evid}-{id}"
            )

    return processeddata, phases



def GetTraceList(event, picks):
    processList = []
    idx = 0
        
    for evid in set(event.event_index):
        picksev = picks[picks["event_index"] == evid]
        for id in set(picksev.id):
        # for id in ['GM.AD07..BH']:
            net, sta, _, _ = id.split('.')
            picksevsta = picksev[picksev['id'] == id]
            phasep = picksevsta[picksevsta['type']=='P']
            if len(phasep) == 0:
                continue
            else:
                starttime = phasep.iloc[0]['timestamp'] - 5*60
                endtime = starttime + 10*60
            processList.append([evid, net, sta, starttime, endtime, idx])
            idx += 1
    
    return np.array(processList)



if __name__ == '__main__':
    # read all data
    if rank == 0:
        station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
        event = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all/catalog_bootstrap_40_1_associated.csv')
        event = event.drop_duplicates(subset=['event_index'])
        event['event_index'] = event['event_index'].astype(int)
        picks = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all/picks_bootstrap_40_1.csv')
        picks = picks[picks.event_index.isin(event.event_index)]
        picks['timestamp'] = picks['timestamp'].apply(lambda x: UTCDateTime(x))
        stead = h5py.File('/mnt/scratch/jieyaqi/alaska/final/Alaska_iter2.hdf5', 'w')
        catalogs = pd.DataFrame()
        phases = pd.DataFrame()
    else:
        station = None
        event = None
        picks = None

    station = comm.bcast(station, root = 0)
    event = comm.bcast(event, root = 0)
    picks = comm.bcast(picks, root = 0)

    # get process list
    if rank == 0:
        processList = GetTraceList(event, picks)
    else:
        processList = None
    processList = comm.bcast(processList, root = 0)
    pool_num = 600
    pool_size = len(processList) // pool_num + bool(len(processList) % pool_num)
    
    if rank == 0:
        logger.info(
            f"{len(processList)} traces need to be processed, each pool has {pool_size} traces")

    i = 0
    while i < pool_num:
        if rank == 0:
            process_index = range(pool_size * i, min(pool_size * (i + 1), len(processList)))
            process_index_this_rank = np.array_split(process_index, size)
        else:
            process_index = None
            process_index_this_rank = None
        process_index_this_rank = comm.scatter(process_index_this_rank, root = 0)

        # Scatter and process data in each rank
        logger.info(f"Rank {rank} starts processing for pool {i}")
        data_this_rank, phase_this_rank = ProcessData(process_index_this_rank, processList, event, picks, station)
        logger.info(f"Rank {rank} finishes processing for pool {i}")
        
        comm.Barrier()
        data_all_rank = comm.gather(data_this_rank, root = 0)
        phase_all_rank = comm.gather(phase_this_rank, root = 0)

        # write hdf5 file and merge dataframe
        if rank == 0:
            for each_data in data_all_rank:
                for evsta, phasedata in each_data.items():
                    evid, id = evsta.split('_')
                    evid = int(evid)
                    net, sta, _, _ = id.split('.')

                    # if event not in dataset, add dataset and metadata
                    if f"/{str(evid)}" not in stead:
                        evdf = event[event['event_index'] == evid]
                        evmeta = {
                            'begin_time': '', 
                            'depth_km': evdf.iloc[0]['depth'], 
                            'end_time': '', 
                            'event_id': evid, 
                            'event_time': evdf.iloc[0]['time'], 
                            'event_time_index': -1, 
                            'latitude': evdf.iloc[0]['latitude'], 
                            'longitude': evdf.iloc[0]['longitude'], 
                            'magnitude': 0, 
                            'magnitude_type': '', 
                            'source': 'ACE'
                            }

                        evdata = stead.create_group(str(evid))
                        for k, v in evmeta.items():
                            evdata.attrs[k] = v
                        catalog = pd.Series(evmeta).to_frame().T
                        catalogs = pd.concat([catalogs, catalog], ignore_index=True)
                
                    # add phase data and meta
                    if phasedata['data'].shape[0] == 3:
                        stadata = evdata.create_dataset(f"/{str(evid)}/{sta}", data = phasedata['data'])
                        for k, v in phasedata['meta'].items():
                            stadata.attrs[k] = v
            temp_list = [phases]
            temp_list.extend(phase_all_rank)
            phases = pd.concat(temp_list, ignore_index=True)
            logger.info(
                f"Pool {i} finished")
        i += 1

    if rank == 0:
        catalogs.to_csv('/mnt/scratch/jieyaqi/alaska/final/catalogs_iter2.csv', sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        phases.to_csv('/mnt/scratch/jieyaqi/alaska/final/phases_iter2.csv', sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        logger.info(f"Saving phases and catalogs")