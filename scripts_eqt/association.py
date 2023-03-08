import numpy as np
import pandas as pd
import obspy
from obspy import UTCDateTime
from pyproj import Proj
from gamma.utils import association
import subprocess
from itertools import repeat
import multiprocessing as mp

def _CalFscore(det: list, obs: list, start: UTCDateTime, end: UTCDateTime, threshold: float):
    TP = []
    FN = []
    FP = []
    utc2str = lambda x: x.__unicode__()

    if det == None or len(det) == 0: 
        if obs == None or len(obs) == 0:
            pass
        else:
            i = 0
            while i < len(obs):
                if obs[i] >= start and obs[i] <= end:
                    FN.append(utc2str(obs[i]))
                i = i + 1
    else:
        if len(obs) == 0:
            FP = [utc2str(i) for i in det]
        else:
            i = j = 0
            TP = []
            FN = []
            FP = []
            
            while i < len(obs) and j < len(det) and obs[i] <= end:
                if obs[i] < start:
                    i = i + 1
                    continue
                elif abs(det[j]-obs[i]) <= threshold:
                    TP.append(utc2str(det[j]))
                    i = i + 1
                    j = j + 1
                elif obs[i] < det[j] - threshold:
                    FN.append(utc2str(obs[i]))
                    i = i + 1
                elif obs[i] > det[j] + threshold:
                    FP.append(utc2str(det[j]))
                    j = j + 1

            while j < len(det):
                FP.append(utc2str(det[j]))
                j = j + 1

            while i < len(obs) and obs[i] <= start:
                FN.append(utc2str(obs[i]))
                i = i + 1
    return TP, FN, FP



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
picks = pd.read_csv('data/ManualPickswamp.csv', delimiter = '\t')
picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x))
picks = picks[picks['timestamp'] > pd.Timestamp(2018, 7, 3)]
picks = picks[picks['timestamp'] < pd.Timestamp(2018, 7, 4)]
event = pd.read_csv('data/events.csv', delimiter='\t')
stations = pd.read_csv('data/stations.csv', delimiter = '\t')
# picks = find_amp(picks, 120, ncpu)
# picks = picks.dropna()

# with open('data/ManualPickswamp.csv', 'w') as fp:
#         picks.to_csv(fp, sep="\t", index=False, 
#                         date_format='%Y-%m-%dT%H:%M:%S.%f')

picks = picks.sort_values("timestamp", ignore_index = True)
up = np.loadtxt("workflow/up.csv")
us = np.loadtxt("workflow/us.csv")
d, Vpv, Vph, Vsv, Vsh = np.loadtxt('workflow/PREM.csv', usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1)
Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)

config = {}
config["center"] = (-156, 55)
config["xlim_degree"] = [-164, -148]
config["ylim_degree"] = [50, 60]
config["starttime"] = UTCDateTime("20180101T00:00:00")
config["endtime"] = UTCDateTime("20200101T00:00:00")
proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
config["dims"] = ['x(km)', 'y(km)', 'z(km)']
xd = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
yd = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
config["x(km)"] = [xd[0], yd[0]]
config["y(km)"] = [xd[1], yd[1]]
config["z(km)"] = (0, 200)
# config["vel"] = {"p": Vp, "s": Vs, "depth": d}
# config["eikonal"] = {"up": up, "us": us}
# config["eikonal_grid"] = 1
config["vel"] = {"p": Vp, "s": Vs, "z": d}
config["eikonal"] = {"xlim": config["x(km)"], 
                     "ylim": config["y(km)"], 
                     "zlim": config["z(km)"], 
                     "h": 1,
                     "vel": config["vel"]}
config["covariance_prior"] = [30, 30]
# config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
config["method"] = "BGMM"
config["oversample_factor"] = 15
config["use_dbscan"] = True
config["use_amplitude"] = True
config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),  # x
    (None, None),  # t
)
config["dbscan_eps"] = 50
config["dbscan_min_samples"] = 3
config["min_picks_per_eq"] = 6
config["max_sigma11"] = 1000
config["max_sigma22"] = 1000
config["max_sigma12"] = 1000
config["ncpu"] = ncpu

stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)

event_idx0 = 0  ## current earthquake index
assignments = []
catalogs, assignments = association(
    picks, 
    stations, 
    config,
    event_idx0,
    method=config["method"],
)
event_idx0 += len(catalogs)


catalogs = pd.DataFrame(catalogs, columns=["time"]+config["dims"]+["magnitude", "sigma_time", "sigma_amp", "cov_time_amp",  "event_index", "gamma_score"])
catalogs[["longitude","latitude"]] = catalogs.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
catalogs["depth(m)"] = catalogs["z(km)"].apply(lambda x: x*1e3)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
picks = picks.merge(stations, "outer", on="id")
picks = picks.dropna()

with open('catalogs0703_gamma.csv', 'w') as fp:
    catalogs.to_csv(fp, sep="\t", index=False, 
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')
with open('picks0703_gamma.csv', 'w') as fp:
    picks.to_csv(fp, sep="\t", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')

event = pd.read_csv('data/events.csv', delimiter = '\t')
event['time'] = event['time'].apply(lambda x: UTCDateTime(x))
catalogs['time'] = catalogs['time'].apply(lambda x: UTCDateTime(x))
catalogs = catalogs.sort_values("time", ignore_index = True)
event = event.sort_values("time", ignore_index = True)
TP, FN, FP = _CalFscore(det = list(catalogs['time']), obs = event['time'], start =  UTCDateTime(2018,1,1), end = UTCDateTime(2020, 1, 1), threshold = 60)
precision = len(TP)/(len(TP)+len(FP))
recall = len(TP)/(len(TP)+len(FN))
F1 = 2/((1/precision) + (1/recall))
print(f'TP:{len(TP)}, FN:{len(FN)}, FP:{len(FP)}, precision: {precision}, recall: {recall}, F1: {F1}')