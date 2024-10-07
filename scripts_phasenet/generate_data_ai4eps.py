import pandas as pd
import h5py
from loguru import logger
import numpy as np
from pathlib import Path
from mpi4py import MPI
import obspy
from obspy import UTCDateTime, read_inventory
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy.clients.fdsn import Client as fdsn_Client
import warnings

warnings.filterwarnings("ignore")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/data.sqlite")
fdsn_client = fdsn_Client("IRIS", timeout=600)
XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")

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
        [event_index, net, sta, starttime, endtime, idx] = processList[processList[:,5] == index][0]
        id = f'{net}.{sta}..BH'
        evdf = event[event['event_index'] == event_index]
        picksevsta = picks[(picks["event_index"] == event_index) & (picks['station'] == sta)]
        picksevsta = picksevsta.sort_values('timestamp')
        picksevsta = picksevsta[(picksevsta['timestamp'] >= starttime) & (picksevsta['timestamp'] <= endtime)]
        pickssta = picks[picks['station'] == sta]
        pickssta = pickssta[(pickssta['timestamp'] >= starttime) & (pickssta['timestamp'] <= endtime)]
        pickssta = pickssta.sort_values('timestamp')

        try:
            st = sq_client.get_waveforms_bulk(
                [("*", sta, "*", "*", starttime - 60, endtime + 60)], None
            )
        except:
            logger.info(
                f"!Error accessing data: {event_index}-{id} {starttime}->{endtime}"
            )
            continue

        ### Process data
        st.detrend("linear")
        st.detrend("demean")

        if st == None or len(st) == 0:
            logger.info(
                f"!Error accessing data: {event_index}-{id} {starttime}->{endtime}")
            continue     
        
        try:
            inv = read_inventory(XMLS/f"{st[0].stats.network}.{st[0].stats.station}.xml")
        except (ValueError, FileNotFoundError):
            # logger.info(
            #             f"Cannot find instrumental response: {net}.{sta} {starttime}->{endtime}")
            # return
            inv = fdsn_client.get_stations(
                    network = st[0].stats.network,
                    station = st[0].stats.station,
                    channel = "HH?,BH?",
                    starttime = starttime,
                    endtime = endtime,
                    level='response'
                )
        try: 
            st.remove_sensitivity(inv)
        except ValueError:
            logger.info(
                f"!Error finding instrumental response: {st[0].stats.network}.{st[0].stats.station,} {starttime}->{endtime}")
            continue

        try:
            st.interpolate(sampling_rate=40)
        except ValueError:
            for tr in st:
                try:
                    tr.interpolate(sampling_rate=40)
                except ValueError:
                    st.remove(tr)
        
        st.merge(method=1, fill_value="latest")

        if st == None or len(st) == 0:
            logger.info(
                f"!Error accessing data: {event_index}-{id} {starttime}->{endtime}")
            continue     

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
                f"!Error accessing data: {event_index}-{id} {starttime}->{endtime}")
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
                f"!Error data length: {event_index} {sta} {starttime}->{endtime}")
            continue
    
        if stadata.shape[0] != 3:
            logger.info(
                f"!Error data shape: {event_index} {sta} {starttime}->{endtime}")
            continue
    
        # double check nan in stadata
        if np.any(np.isnan(stadata)):
            stadata = np.nan_to_num(stadata, nan = 0, posinf = 0, neginf = 0)

        phase_index = ((pickssta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)
        picksevsta['phase_index'] = picksevsta['timestamp'].apply(lambda x: int((x - starttime) / st[0].stats.delta))
        if len(picksevsta[picksevsta['type'] == 'P']) > 0:
            p_phase = picksevsta[picksevsta['type'] == 'P'].sort_values('timestamp').iloc[0]
        else:
            p_phase = None
        if picksevsta[picksevsta['type'] == 'S'] > 0:
            s_phase = picksevsta[picksevsta['type'] == 'S'].sort_values('timestamp').iloc[0]
        else:
            s_phase = None
        stainfo = station[station['id'] == id]
        if len(stainfo) == 0:
            stainfo = station[station['station'] == sta]
        if len(stainfo) == 0:
            logger.info(
                f"!Station out of region: {event_index} {sta} {starttime}->{endtime}")
            continue
        dist, backazimuth, azimuth = obspy.geodetics.base.gps2dist_azimuth(stainfo.iloc[0]['latitude'], stainfo.iloc[0]['longitude'], evdf.iloc[0]['latitude'], evdf.iloc[0]['longitude'])
    
        stameta = {
            'network': st[0].stats.network, 
            'station': st[0].stats.station, 
            'location': st[0].stats.location, 
            'instrument': st[0].stats.channel[:2],
            'component': ''.join(channels), 
            'latitude': stainfo.iloc[0]['latitude'], 
            'longitude': stainfo.iloc[0]['longitude'], 
            'elevation_m': stainfo.iloc[0]['elevation(m)'], 
            # 'local_depth_m': 0.0, 
            'distance_km': round(dist/1000, 4), 
            # 'takeoff_angle': -1, 
            'azimuth': round(azimuth, 4), 
            'back_azimuth': round(backazimuth, 4), 
            'dt_s': st[0].stats.delta, 
            'unit': 'm/s',
            'snr': CalSNR(np.array(stadata), phase_index, 10),
            'p_phase_index': p_phase['phase_index'] if p_phase != None else -1,
            's_phase_index': s_phase['phase_index'] if s_phase != None else -1,
            'p_phase_score': 1.0 if p_phase != None else 0,
            's_phase_score': 1.0 if s_phase != None else 0,
            'p_phase_time': str(p_phase['timestamp'])[:-1] if p_phase != None else '',
            's_phase_time': str(s_phase['timestamp'])[:-1] if s_phase != None else '',
            'p_phase_source': 'manual',
            's_phase_source': 'manual',
            'phase_type': [str(x) for x in pickssta['type']], 
            'phase_index': phase_index, 
            'phase_score': [1] * len(pickssta), 
            'phase_time': [str(x)[:-1] for x in pickssta['timestamp']], 
            'event_id': list(pickssta['event_index']), 
            }

        phase_index_ev = ((picksevsta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)
        phase = pd.DataFrame({
            'event_id': [event_index] * len(picksevsta),
            'station_id': [f'{st[0].stats.network}.{st[0].stats.station}.{st[0].stats.location}.{st[0].stats.channel[:2]}'] * len(picksevsta),
            'phase_index': phase_index_ev,
            'phase_time': [str(x)[:-1] for x in picksevsta['timestamp']],
            'phase_score': [1] * len(picksevsta),
            'phase_type': [str(x) for x in picksevsta['type']],
        })

        processeddata[f'{event_index}_{st[0].stats.network}.{st[0].stats.station}.{st[0].stats.location}.{st[0].stats.channel[:2]}'] = {'data': stadata, 'meta': stameta, 'starttime': starttime, 'endtime': endtime}
        phases = pd.concat([phases, phase], ignore_index=True)
    
        logger.info(
                f"{rank}: {idx}/{len(processList)} Processed {event_index}-{id}"
            )

    return processeddata, phases



def get_start_end(picksev, station, evlat, evlon):
    picksev_ev = picksev.merge(station, how='inner', on='station')
    picksev_ev['dist'] = picksev_ev.apply(lambda x: obspy.geodetics.base.gps2dist_azimuth(x['latitude'], x['longitude'], evlat, evlon)[0]/1000, axis=1)
    picksev_ev = picksev_ev.sort_values('dist')
    for _, row in picksev_ev.iterrows():
        if row['type'] == 'P':
            return row['timestamp']-180, row['timestamp']+420



def GetTraceList(event, picks, station):
    processList = []
    idx = 0
        
    for _, row in event.iterrows():
    # for _, row in event.iloc[0:1].iterrows():
        event_index = row['event_index']
        evlat = row['latitude']
        evlon = row['longitude']
        picksev = picks[picks["event_index"] == event_index]
        starttime, endtime = get_start_end(picksev, station, evlat, evlon)
        for id in set(picksev.id):
            net, sta, _, _ = id.split('.')
            picksevsta = picksev[picksev['station'] == sta]
            phasep = picksevsta[picksevsta['type']=='P']
            if len(phasep) == 0:
                continue
            processList.append([event_index, net, sta, starttime, endtime, idx])
            idx += 1
    
    return np.array(processList)



if __name__ == '__main__':
    # read all data
    if rank == 0:
        station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
        station['station'] = station['id'].apply(lambda x: x.split('.')[1])
        event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
        picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks.csv')
        picks = picks[picks.event_index.isin(event.event_index)]
        picks['timestamp'] = picks['timestamp'].apply(lambda x: UTCDateTime(x))
        outdir = Path('/mnt/scratch/jieyaqi/alaska/final/PS_Alaska/ManualPick_ai4eps')
        stead = h5py.File(outdir / 'waveform_all.h5', 'w')
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
        processList = GetTraceList(event, picks, station)
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
                    event_index, id = evsta.split('_')
                    net, sta, _, _ = id.split('.')

                    # if event not in dataset, add dataset and metadata
                    if f"/{str(event_index)}" not in stead:
                        evdf = event[event['event_index'] == event_index]
                        evtime = UTCDateTime(evdf.iloc[0]['time'])
                        evindex = int(((evtime - phasedata['starttime']) * 40))
                        evmeta = {
                            'event_id': event_index, 
                            'event_time': str(evtime)[:-1], 
                            'event_time_index': evindex, 
                            'begin_time': str(phasedata['starttime'])[:-1], 
                            'end_time': str(phasedata['endtime'])[:-1], 
                            'latitude': evdf.iloc[0]['latitude'], 
                            'longitude': evdf.iloc[0]['longitude'], 
                            'depth_km': evdf.iloc[0]['depth'], 
                            'magnitude': evdf.iloc[0]['magnitude'], 
                            'magnitude_type': "Mw",
                            'sampling_rate': 40,
                            'nt': 24000,
                            'nx': 1, 
                            'source': 'AEC'
                            }

                        evdata = stead.create_group(str(event_index))
                        for k, v in evmeta.items():
                            evdata.attrs[k] = v
                    else:
                        stead[event_index].attrs['nx'] += 1
                
                    # add phase data and meta
                    if phasedata['data'].shape[0] == 3:
                        stadata = stead.create_dataset(f"/{str(event_index)}/{id}", data = phasedata['data'])
                        for k, v in phasedata['meta'].items():
                            stadata.attrs[k] = v
            temp_list = [phases]
            temp_list.extend(phase_all_rank)
            phases = pd.concat(temp_list, ignore_index=True)
            logger.info(
                f"Pool {i} finished")
        i += 1

    if rank == 0:
        for k in stead.keys():
            evmeta = dict(stead[k].attrs)
            catalog = pd.Series(evmeta).to_frame().T
            catalogs = pd.concat([catalogs, catalog], ignore_index=True)
        catalogs = catalogs[['event_id', 'event_time', 'latitude', 'longitude', 'depth_km', 'magnitude', 'magnitude_type', 'source']]
        catalogs.rename(columns={'event_time':'time'})
        catalogs.to_csv(outdir / 'catalogs.csv', sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        phases.to_csv(outdir / 'phase_picks.csv', sep=",", index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')
        logger.info(f"Saving phases and catalogs")

        group_names = list(stead.keys())
        f = h5py.File(outdir / 'waveform.h5', 'w')
        for group_name in group_names:
            output_file_path = f / 'waveform' / f"{group_name}.h5"
        
            with h5py.File(output_file_path, "w") as output_h5_file:
                stead.copy(group_name, output_h5_file)
            f[group_name] = h5py.ExternalLink(f'waveform/{group_name}.h5', f'/{group_name}')