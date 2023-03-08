import pandas as pd
import h5py
import obspy
import subprocess
import random
import numpy as np
import os
from itertools import repeat
import multiprocessing as mp



def Findfile(file):
    result = subprocess.run(file, capture_output=True, shell=True, text=True)
    if not result.stderr:
        return result.stdout.strip()
    else:
        return None



def CalSNR(data, ssample, window = 4):
    snr = []
    for tr in data:
        n = np.percentile(tr[0:window*100], 95)
        s = np.percentile(tr[ssample: ssample + window*100], 95)
        snr.append(10 * np.log10(s**2 / n**2))
    return np.array(snr)



def GetCoda(data, ssample, window = 3):
    s = np.average(data[0][ssample: ssample + window*100]**2)
    i = ssample
    while i < len(data[0]) - window*100:
        tmp = np.average(data[0][i: i + window*100]**2)
        if tmp < s / 64:
            return np.array([[i]])
        else:
            i = i + 1 * 100
    return 'none'



def GenerateRandT(t, length):
    start = obspy.UTCDateTime(int(t[:4]), int(t[4:6]), 1)
    newt = start + random.randrange(31 * 24 * 60 * 60)
    if newt.month == int(t[4:6]) and (newt + length).month == int(t[4:6]):
        return newt
    else:
        GenerateRandT(t, length)



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



def CheckNoEvent(start, picks, length):
    pickstmp = picks[picks['timestamp'] > pd.Timestamp((start - 2*60).strftime('%Y-%m-%dT%H:%M:%S'))]
    pickstmp = pickstmp[pickstmp['timestamp'] < pd.Timestamp((start+length+2*60).strftime('%Y-%m-%dT%H:%M:%S'))]

    if len(pickstmp) == 0:
        return True
    else:
        return False



def CheckWaveform(data, window = 3):
    min = np.inf
    max = 0
    i = 0
    while i < len(data) - window*100:
        tmp = np.average(data[i: i + window*100]**2)
        if tmp < min:
            min = tmp
        elif tmp > max:
            max = tmp
        i = i + 1 * 100
    
    if max/min > 16:
        return False
    else:
        return True



def NoisePerSta(sta, picks, station, config):
    datadir = config['datadir']
    num = config['num']
    length = config['length']

    stead = h5py.File(f'/mnt/scratch/jieyaqi/alaska/SteadData/AlaskaNoise{sta}.hdf5', 'w')
    noisedata = stead.create_group("non_earthquake/noise")
    steadcsv = pd.DataFrame()

    wavelist = os.listdir(os.path.join(datadir, sta))
    id = wavelist[0].split('__')[0][:-1]
    stainfo = station[station['id']==id]
    [net, sta, loc, cha] = id.split('.')
    timel = set([w.split('__')[1] for w in wavelist])
    # numpertr = int(np.ceil(num/len(timel)))
    numpertr = num
    
    for time in timel:
        filez = Findfile(f'ls {datadir}/{sta}/{id}Z__{time}*')
        filee = Findfile(f'ls {datadir}/{sta}/{id}[E,1]__{time}*')
        filen = Findfile(f'ls {datadir}/{sta}/{id}[N,2]__{time}*')

        if filez == None or filee == None or filen == None:
            continue

        stz = Processdata(filez)
        ste = Processdata(filee)
        stn = Processdata(filen)

        i = 0
        while i < numpertr:
            startt = GenerateRandT(time, length)
            if not CheckNoEvent(startt, picks[picks['id'] == id], length):
                continue

            starttstr = startt.strftime('%Y%m%d%H%M%S')

            dataZ, realstartZ = GetData(stz, startt, length)
            dataE, realstartE = GetData(ste, startt, length)
            dataN, realstartN = GetData(stn, startt, length)
            

            if type(dataZ).__module__ != np.__name__ or type(dataE).__module__ != np.__name__ or type(dataN).__module__ != np.__name__:
                continue

            if not CheckWaveform(dataZ):
                continue
            
            try:
                data = np.array([dataZ[:length*100], dataE[:length*100], dataN[:length*100]])
            except ValueError:
                print(f'{net}.{sta}_{starttstr}_NO')

            steadev = noisedata.create_dataset(f'{net}.{sta}_{starttstr}_NO', data = np.stack(data, axis = -1)[0:length*100])

            steadev.attrs['network_code'] = net
            steadev.attrs['receiver_code'] = sta
            steadev.attrs['receiver_elevation_m'] = stainfo['elevation(m)'].array[0]
            steadev.attrs['receiver_latitude'] = stainfo['latitude'].array[0]
            steadev.attrs['receiver_longitude'] = stainfo['longitude'].array[0]
            steadev.attrs['receiver_type'] = cha
            steadev.attrs['trace_category'] = 'noise'
            steadev.attrs['trace_name'] = steadev.name
            steadev.attrs['trace_start_time'] = realstartZ
            i = i + 1

            series = pd.Series(steadev.attrs).to_frame().T
            steadcsv = pd.concat([steadcsv, series], ignore_index=True)
        break

    steadcsv.to_csv(f'/mnt/scratch/jieyaqi/alaska/SteadData/AlaskaNoise{sta}.csv', 
                    sep="\t", 
                    index=False, 
                    date_format='%Y-%m-%dT%H:%M:%S.%f')



if __name__ == '__main__':
    
    picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/ManualPickswamp.csv', delimiter = '\t')
    picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x))
    station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv', delimiter = '\t')
    event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv', delimiter = '\t')
    config = {'length': 120, 'num': 5, 'datadir': '/mnt/scratch/jieyaqi/alaska/waveform'}

    with mp.Pool(20) as p:
        p.starmap(NoisePerSta, zip(set(os.listdir(os.path.join(config['datadir']))), repeat(picks), repeat(station), repeat(config)))
        
