import numpy as np
import pandas as pd
import obspy
from obspy import UTCDateTime
from pyproj import Proj
from gamma.utils import association
import subprocess
from itertools import repeat
import multiprocessing as mp
from collections import defaultdict
import time

def CalFscore(gamma_picks):
    event_id_pool=set(gamma_picks.event_id)
    event_index_pool=set(gamma_picks.event_index)
    event_index = event_index_pool.difference(-1)

    counter=defaultdict(int)
    def count_func(row):
        if row.event_index!=-1:
            counter[(row.event_id,row.event_index)]+=1

    gamma_picks.apply(count_func,axis=1)
    status=[]
    for key in counter:
        status.append([counter[key],key[0],key[1]])
    status.sort(reverse=True)

    mapper={}
    for _,event_id,event_index in status:
        if event_id in event_id_pool and event_index in event_index_pool:
            mapper[event_id]=event_index
            event_id_pool.remove(event_id)
            event_index_pool.remove(event_index)

    # tp: row in gamma_picks satisfy mapper
    # fp: row in gamma_picks not satisfy mapper
    # fn: event_index is -1
    tp,fp,fn=[0],[0],[0]
    def count_confusion(row):
        if row.event_index==-1:
            fn[0]+=1
        elif row.event_id in mapper and mapper[row.event_id]==row.event_index:
            tp[0]+=1
        else:
            fp[0]+=1
    gamma_picks.apply(count_confusion,axis=1);

    precision=tp[0]/(tp[0]+fp[0])
    recall=tp[0]/(tp[0]+fn[0])
    f1=2*precision*recall/(precision+recall)
    print("precision: ",precision)
    print("recall: ",recall)
    print("f1: ",f1)

    print("tp: ",tp[0])
    print("fp: ",fp[0])
    print("fn: ",fn[0])
    return 



def _find_amp_sta(id, picks, window, lock, pickwamp):
    datadir = '/mnt/scratch/jieyaqi/alaska/waveform'
    filename = ''
    picksid = picks[picks["id"] == id]
    picksid = picksid.sort_values("timestamp", ignore_index = True)
    [net, sta, loc, cha] = id.split('.')
    for i in range(len(picksid)):
        tarrival = picksid.iloc[i].timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        t0 = picksid.iloc[i].timestamp.strftime('%Y%m')
        result = subprocess.run(f'ls {datadir}/{sta}/{net}.{sta}*{cha}Z__{t0}01T000000Z__*', capture_output=True, shell=True, text=True)

        if not result.stderr:
            cfile = result.stdout.strip()
        else:
            continue

        if cfile != filename:
            st = obspy.read(cfile)
            st.detrend('demean')
            st.detrend('linear')
            st.taper(max_percentage=0.001, type='cosine', max_length=2)
            st.filter(type='bandpass', freqmin = 1.0, freqmax = 45, corners=2, zerophase=True)
            filename = cfile

        t = obspy.UTCDateTime(tarrival)
        for tr in st:
            if t > tr.stats.starttime and t + window < tr.stats.endtime:
                delta = tr.stats.delta
                ib = int((t - tr.stats.starttime) / delta)
                ie = int((t - tr.stats.starttime + window) / delta)
                amp = max(np.abs(tr.data[ib:ie]))
                picksid.loc[i, 'amp'] = amp/1e9
                break
    
    with lock:
        pickwamp.df = pd.concat([picksid, pickwamp.df])
    return



def find_amp(picks, window = 12, ncpu = 10):
    '''
    Find the amplitude of arrival
    Parameter
    ---------
    st: obspy.stream
    arrival: pd.object
    '''

    idl = set(picks.id)

    manager = mp.Manager()
    lock = manager.Lock()
    pickwamp = manager.Namespace()
    pickwamp.df = pd.DataFrame()

    with mp.Pool(ncpu) as p:
        p.starmap(_find_amp_sta, zip(idl, repeat(picks), repeat(window), repeat(lock), repeat(pickwamp)))
    
    return pickwamp.df

ncpu = 20
# picks = pd.read_csv('/mnt/scratch/jieyaqi/alaska/eqt/picks.csv')
picks = pd.read_csv('data/manualPicks.csv')
picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x[:-1]))
picks['prob'] = 1
# for test: 2018-10-19T00:14:10.815000Z
# picks = picks[picks['timestamp'] > pd.Timestamp(2018, 10, 19, 0, 14)]
# picks = picks[picks['timestamp'] < pd.Timestamp(2018, 10, 19, 0, 20)]
# picks = picks[picks['timestamp'] >= pd.Timestamp(2018, 6, 1, 7, 51)]
# picks = picks[picks['timestamp'] < pd.Timestamp(2018, 6, 1, 8, 1)]
event = pd.read_csv('data/events.csv', delimiter='\t')
stations = pd.read_csv('data/stations.csv')
# picks = find_amp(picks, 120, ncpu)
# picks = picks.dropna()

picks = picks.sort_values("timestamp", ignore_index = True)
d, Vpv, Vph, Vsv, Vsh = np.loadtxt("scripts_eqt/PREM.csv", usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1)
Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)

config = {}
config["center"] = (-156, 55)
config["xlim_degree"] = [-165, -147]
config["ylim_degree"] = [50, 60]
config["starttime"] = UTCDateTime("20190101T00:00:00")
config["endtime"] = UTCDateTime("20190301T00:00:00")
proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
config["dims"] = ['x(km)', 'y(km)', 'z(km)']
xd = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
yd = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
config["x(km)"] = [xd[0], yd[0]]
config["y(km)"] = [xd[1], yd[1]]
config["z(km)"] = (0, 400)

config["eikonal"] = {"xlim": config["x(km)"], 
                     "ylim": config["y(km)"], 
                     "zlim": config["z(km)"], 
                     "h": 1,
                     "vel": {"p": Vp, "s": Vs, "z": d}}
config["covariance_prior"] = [300, 300]
# config['initial_points'] = [1, 1, 4]
config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
config["method"] = "BGMM"
config["oversample_factor"] = 20
config["use_dbscan"] = True
config["use_amplitude"] = False
config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),  # x
    (None, None),  # t
)
config['initial_points'] = [1, 1, 2]
config["dbscan_eps"] = 50
config["dbscan_min_samples"] = 3
config["min_picks_per_eq"] = 5
config["min_p_picks_per_eq"] = 3
config["min_s_picks_per_eq"] = 3
config["max_sigma11"] = 5
config["max_sigma22"] = 5
config["max_sigma12"] = 5
config["ncpu"] = ncpu

stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)

event_idx0 = 0  ## current earthquake index
assignments = []
start = time.time()
catalogs, assignments = association(
    picks, 
    stations, 
    config,
    event_idx0,
    method=config["method"],
)
end = time.time()
print(f"Association time: {(end - start)/60}")
event_idx0 += len(catalogs)


catalogs = pd.DataFrame(catalogs, columns=["time"]+config["dims"]+["magnitude", "sigma_time", "sigma_amp", "cov_time_amp",  "event_index", "gamma_score"])
catalogs[["longitude","latitude"]] = catalogs.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
catalogs["depth(m)"] = catalogs["z(km)"].apply(lambda x: x*1e3)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
picks = picks.merge(stations, "outer", on="id")
picks = picks.dropna()

with open('catalogs_gamma_test.csv', 'w') as fp:
# with open('/mnt/scratch/jieyaqi/alaska/eqt/catalogs_gamma.csv', 'w') as fp:
    catalogs.to_csv(fp, index=False, 
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')
with open('picks_gamma_test.csv', 'w') as fp:
# with open('/mnt/scratch/jieyaqi/alaska/eqt/picks_gamma.csv', 'w') as fp:
    picks.to_csv(fp, index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')