import pandas as pd
import h5py
from loguru import logger
from pathlib import Path
import numpy as np
import multiprocessing as mp
from obspy import UTCDateTime, read_inventory
from obspy.clients.iris import Client as iris_Client
from obspy.clients.filesystem.tsindex import Client as sql_Client
from obspy.clients.fdsn import Client as fdsn_Client
from obspy.taup import TauPyModel
model = TauPyModel(model="PREM")

iris_client = iris_Client(timeout =600)
fdsn_client = fdsn_Client("IRIS", timeout=600)
XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")



def CalSNR(data, phase_index, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(np.abs(tr[0:window*40]), 95) + 1e-6
        s = np.percentile(np.abs(tr[max(phase_index): max(phase_index) + window*40]), 95) + 1e-6
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def ProcessData(st, starttime, endtime):

    channels = []
    for tr in st:
        channels.append(tr.stats.channel[2])
    channels = set(channels)

    if ('Z' not in channels) or ('E' not in channels) or ('N' not in channels):
        return None
    
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")

    pre_filt = [0.01, 0.05, 20, 50]

    try:
        inv = read_inventory(XMLS/f"{st[0].stats.network}.{st[0].stats.station}.xml")
        st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                    taper=False, inventory=inv)
    except (ValueError, FileNotFoundError):
        # logger.info(
        #             f"Cannot find instrumental response: {net}.{sta} {starttime}->{endtime}")
        # return
        inv = fdsn_client.get_stations(
                network = st[0].stats.network,
                station = st[0].stats.station,
                channel = "HH?,BH?,EH?,SH?",
                starttime = starttime,
                endtime = endtime,
                level='response'
            )
        try:
            st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                        taper=False, inventory=inv)
        except ValueError:
            logger.info(
                        f"!Error finding instrumental response: {st[0].stats.network}.{st[0].stats.station,} {starttime}->{endtime}")
            return
        
    try:
        st.interpolate(sampling_rate=40)
    except ValueError:
        for tr in st:
            try:
                tr.interpolate(sampling_rate=40)
            except ValueError:
                st.remove(tr)
        
    st.merge(method=1, fill_value=0)
        
    st.trim(starttime, endtime)

    if len(st) == 0:
        return None
    
    # # padding other channels
    # channels = []
    # for tr in st:
    #     channels.append(tr.stats.channel[2])

    # if 'Z' not in channels:
    #     trz = st[0].copy()
    #     trz.data = np.zeros(len(trz.data))
    #     trz.stats.channel = st[0].stats.channel[:2] + 'Z'
    #     st.append(trz)

    # if 'E' not in channels and '1' not in channels:
    #     tre = st[0].copy()
    #     tre.data = np.zeros(len(tre.data))
    #     tre.stats.channel = st[0].stats.channel[:2] + 'E'
    #     st.append(tre)

    # if 'N' not in channels and '2' not in channels:
    #     trn = st[0].copy()
    #     trn.data = np.zeros(len(trn.data))
    #     trn.stats.channel = st[0].stats.channel[:2] + 'N'
    #     st.append(trn)

    return st



def DataPerEv(evid, picks, station, event, stead, catalogs, phases):
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
    sq_client = sql_Client("/mnt/scratch/jieyaqi/alaska/timeseries.sqlite")
    evdata = stead.create_group(evid)
    for k, v in evmeta.items():
        evdata.attrs[k] = v
    catalog = pd.Series(evmeta).to_frame().T
    catalogs = pd.concat([catalogs, catalog], ignore_index=True)

    picksev = picks[picks["evid"] == evid]
    # for sta in ['CHI']:
    for sta in set(picksev.station):
        print(evid, sta)
        picksevsta = picksev[picksev['station'] == sta]
        picksevsta['timestamp'] = picksevsta['timestamp'].apply(lambda x: UTCDateTime(x))
        picksevsta = picksevsta.sort_values('timestamp')

        id = picksevsta.iloc[0]['id']
        phasep = picksevsta[picksevsta['type']=='P']
        if len(phasep) == 0:
            continue
        else:
            starttime = phasep.iloc[0]['timestamp'] - 5*60
            endtime = starttime + 10*60
        picksevsta[picksevsta['timestamp'] <= endtime]

        try:
            st = sq_client.get_waveforms(
                "*", sta, "*", "*", starttime - 60, endtime + 60
            )
        except:
            logger.info(
                f"!Error accessing data: {sta} {starttime}->{endtime}"
            )
            continue

        if len(st) == 0:
            logger.info(
                f"!Error accessing data: {sta} {starttime}->{endtime}")
            continue

        st = ProcessData(st, starttime, endtime)
        if st == None or len(st[0].data) < (endtime-starttime) * 40:
            logger.info(
                f"!Error data length: {sta} {starttime}->{endtime}")
            continue            
        try:
            stadata = evdata.create_dataset(sta, data = np.stack([tr.data for tr in st])[:, :24000])
        except ValueError:
            logger.info(
                f"!Error data length: {sta} {starttime}->{endtime}")
            continue
        phase_index = ((picksevsta['timestamp'].to_numpy() - starttime) / st[0].stats.delta).astype(int)

        stainfo = station[station['id'] ==  id]
        dist = iris_client.distaz(
            stalat = stainfo.iloc[0]['latitude'], 
            stalon = stainfo.iloc[0]['longitude'], 
            evtlat = evmeta['latitude'], 
            evtlon = evmeta['longitude'])
        
        stameta = {
            'azimuth': dist['azimuth'], 
            'back_azimuth': dist['backazimuth'], 
            'begin_time': str(starttime), 
            'component': [tr.stats.channel[2] for tr in st], 
            'distance_km': dist['distancemeters']/1000, 
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

        for k, v in stameta.items():
            stadata.attrs[k] = v

        phase = pd.DataFrame({
            'event_id': [evid] * len(picksevsta),
            'station_id': [st[0].stats.station] * len(picksevsta),
            'phase_index': phase_index,
            'phase_time': [str(x) for x in picksevsta['timestamp']],
            'phase_score': [1] * len(picksevsta),
            'phase_type': [str(x) for x in picksevsta['type']],
            'phase_polarity': [''] * len(picksevsta)
        })
        phases = pd.concat([phases, phase], ignore_index=True)

    return catalogs, phases


if __name__ == '__main__':
    picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manualPicks.csv')
    station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
    event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv', delimiter = '\t')
    datadir = '/mnt/scratch/jieyaqi/alaska/waveform'
    stead = h5py.File(f'/mnt/scratch/jieyaqi/alaska/phasenet/dataset/Alaska.hdf5', 'w')
    catalogs = pd.DataFrame()
    phases = pd.DataFrame()

    for evid in set(event.evid):
    # for evid in ['0195gt0rv3']:
        catalogs, phases = DataPerEv(evid, picks, station, event, stead, catalogs, phases)

    with open(f'/mnt/scratch/jieyaqi/alaska/phasenet/dataset/catalogs.csv', 'w') as fp:
        catalogs.to_csv(fp, sep=",", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')
    
    with open(f'/mnt/scratch/jieyaqi/alaska/phasenet/dataset/phases.csv', 'w') as fp:
        phases.to_csv(fp, sep=",", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')