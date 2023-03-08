import pandas as pd
import h5py
import obspy
import subprocess
import random
import numpy as np
from itertools import repeat
import multiprocessing as mp
from obspy.clients.iris import Client
from obspy.taup import TauPyModel
model = TauPyModel(model="PREM")
client = Client()



def Findfile(file):
    result = subprocess.run(file, capture_output=True, shell=True, text=True)
    if not result.stderr:
        return result.stdout.strip()
    else:
        return None
    


def Processdata(file):
    st = obspy.read(file)
    st.detrend('demean')
    st.detrend('linear')
    st.taper(max_percentage=0.001, type='cosine', max_length=2)
    st.filter(type='bandpass', freqmin = 1.0, freqmax = 45, corners=2, zerophase=True)
    st.resample(100.0, window='hann')
    return st



def GetData(st, startt, length):
    for tr in st:
        if startt > tr.stats.starttime and startt + length < tr.stats.endtime:
            ib = int((startt - tr.stats.starttime) / 0.01)
            ie = int((startt - tr.stats.starttime + length) / 0.01)
            data = tr[ib: ie + 1]
            return data, (tr.stats.starttime + ib*0.01).strftime('%Y-%m-%d %H:%M:%S.%f')
    return None, None



def CalSNR(data, ssample, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(np.abs(tr[0:window*100]), 95) + 1e-6
        s = np.percentile(np.abs(tr[ssample: ssample + window*100]), 95) + 1e-6
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def GetCoda(data, snr, ssample, window = 3):
    s = np.average(data[ssample: ssample + window*100]**2)
    i = ssample
    while i < len(data) - window*100:
        tmp = np.average(data[i: i + window*100]**2)
        if tmp < s / (snr/3)**2:
            return np.array([[i]])
        else:
            i = i + 1 * 100
    return 'None'



def DataPerSta(id, picks, station, event, config):
    picksta = picks[picks["id"] == id]
    picksta = picksta.sort_values("timestamp", ignore_index = True)
    [net, sta, loc, cha] = id.split('.')
    stainfo = station[station['id']==id]
    length = config['length']
    datadir = config['datadir']
    stead = h5py.File(f'/mnt/scratch/jieyaqi/alaska/SteadData/Alaska{sta}.hdf5', 'w')
    steaddata = stead.create_group("earthquake/local")
    steadcsv = pd.DataFrame()

    filename = ''
    for i in range(len(event)):
        evid = event.loc[i, 'evid']
        pickstaev = picksta[picksta['evid'] == evid]
        if len(pickstaev) == 0:
            continue
        
        try:
            parrival = pickstaev[pickstaev['type'] == 'P']['timestamp'].array[0].strftime('%Y-%m-%dT%H:%M:%S.%f')
        except IndexError:
            parrival = None

        try:    
            sarrival = pickstaev[pickstaev['type'] == 'S']['timestamp'].array[0].strftime('%Y-%m-%dT%H:%M:%S.%f')
        except IndexError:
            sarrival = None
        
        pad = random.randint(5, 10+1)
        dist = client.distaz(stalat = stainfo.latitude.array[0], stalon = stainfo.longitude.array[0], evtlat = event.loc[i, 'latitude'], evtlon = event.loc[i, 'longitude'])
        
        if parrival == None:
            theop = model.get_travel_times(source_depth_in_km=event.loc[i, 'depth'], distance_in_degree = dist['distance'], phase_list=['p', 'P'])
            startt = obspy.UTCDateTime(event.loc[i, 'time']) + theop[0].time - pad
        else:
            startt = obspy.UTCDateTime(parrival) - pad

        if sarrival == None:
            theos = model.get_travel_times(source_depth_in_km=event.loc[i, 'depth'], distance_in_degree = dist['distance'], phase_list=['s', 'S'])
            ssample = int((obspy.UTCDateTime(event.loc[i, 'time']) + theos[0].time - startt) / 0.01)
        else:
            ssample = int((obspy.UTCDateTime(sarrival) - startt) / 0.01)

        t0 = startt.strftime('%Y%m')
        starttstr = startt.strftime('%Y%m%d%H%M%S')

        filez = Findfile(f'ls {datadir}/{sta}/{net}.{sta}*{cha}Z__{t0}01T000000Z__*')
        filee = Findfile(f'ls {datadir}/{sta}/{net}.{sta}*{cha}[E,1]__{t0}01T000000Z__*')
        filen = Findfile(f'ls {datadir}/{sta}/{net}.{sta}*{cha}[N,2]__{t0}01T000000Z__*')
        
        if filez == None or filee == None or filen == None:
            onecom = onecom + 1
            continue

        if filez != filename:
            stz = Processdata(filez)
            ste = Processdata(filee)
            stn = Processdata(filen)

            filename = filez
        
        dataZ, realstartZ = GetData(stz, startt, length)
        dataE, realstartE = GetData(ste, startt, length)
        dataN, realstartN = GetData(stn, startt, length)

        if type(dataZ).__module__ != np.__name__ or type(dataE).__module__ != np.__name__ or type(dataN).__module__ != np.__name__:
            continue
        
        try:
            data = np.array([dataZ[:length*100], dataE[:length*100], dataN[:length*100]])
        except ValueError:
            print(f'{net}.{sta}_{starttstr}_EV')

        snr = CalSNR(data, ssample)
        coda = GetCoda(data[np.argmax(snr)], snr[np.argmax(snr)], ssample)
        steadev = steaddata.create_dataset(f'{net}.{sta}_{starttstr}_EV', data = np.stack(data, axis = -1)[0:length*100])
        
        if parrival != None:
            steadev.attrs['p_arrival_sample'] = pad * 100
            steadev.attrs['p_status'] = 'manual'
            steadev.attrs['p_travel_sec'] = obspy.UTCDateTime(parrival) - obspy.UTCDateTime(event.loc[i, 'time'])
        else:
            steadev.attrs['p_arrival_sample'] = 'None'
            steadev.attrs['p_status'] = 'None'
            steadev.attrs['p_travel_sec'] = 'None'
        steadev.attrs['p_weight'] = 1

        if sarrival != None:
            steadev.attrs['s_arrival_sample'] = int((obspy.UTCDateTime(sarrival) - startt) / 0.01)
            steadev.attrs['s_status'] = 'manual'
        else:
            steadev.attrs['s_arrival_sample'] = 'None'
            steadev.attrs['s_status'] = 'None'
        steadev.attrs['s_weight'] = 1

        steadev.attrs['back_azimuth_deg'] = dist['backazimuth']
        steadev.attrs['coda_end_sample'] = coda
        steadev.attrs['network_code'] = net
        steadev.attrs['receiver_code'] = sta
        steadev.attrs['receiver_elevation_m'] = stainfo['elevation(m)'].array[0]
        steadev.attrs['receiver_latitude'] = stainfo['latitude'].array[0]
        steadev.attrs['receiver_longitude'] = stainfo['longitude'].array[0]
        steadev.attrs['receiver_type'] = cha
        steadev.attrs['snr_db'] = snr
        
        steadev.attrs['source_depth_km'] = event.loc[i, 'depth']
        steadev.attrs['source_depth_uncertainty_km'] = 'None'
        steadev.attrs['source_distance_deg'] = dist['distance']
        steadev.attrs['source_distance_km'] = dist['distancemeters']/1000
        steadev.attrs['source_error_sec'] = 'None'
        steadev.attrs['source_gap_deg'] = 'None'
        steadev.attrs['source_horizontal_uncertainty_km'] = 'None'
        steadev.attrs['source_id'] = event.loc[i, 'evid']
        steadev.attrs['source_latitude'] = event.loc[i, 'latitude']
        steadev.attrs['source_longitude'] = event.loc[i, 'longitude']
        steadev.attrs['source_magnitude'] = event.loc[i, 'magnitude']
        steadev.attrs['source_magnitude_author'] = 'None'
        steadev.attrs['source_magnitude_type'] = 'None'
        steadev.attrs['source_mechanism_strike_dip_rake'] = 'None'
        steadev.attrs['source_origin_time'] = event.loc[i, 'time'].replace('T', ' ')[:-1]
        steadev.attrs['source_origin_uncertainty_sec'] = 'None'

        steadev.attrs['trace_category'] = 'earthquake_local'
        steadev.attrs['trace_name'] = steadev.name
        steadev.attrs['trace_start_time'] = realstartZ

        series = pd.Series(steadev.attrs).to_frame().T
        steadcsv = pd.concat([steadcsv, series], ignore_index=True)
    
    with open(f'/mnt/scratch/jieyaqi/alaska/SteadData/Alaska{sta}.csv', 'w') as fp:
        steadcsv.to_csv(fp, sep="\t", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')

    return


if __name__ == '__main__':
    picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/ManualPickswamp.csv', delimiter = '\t')
    picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x))
    station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv', delimiter = '\t')
    event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv', delimiter = '\t')
    config = {'length': 120, 'datadir': '/mnt/scratch/jieyaqi/alaska/waveform'}
    
    with mp.Pool(20) as p:
        p.starmap(DataPerSta, zip(set(picks.id), repeat(picks), repeat(station), repeat(event), repeat(config)))
        