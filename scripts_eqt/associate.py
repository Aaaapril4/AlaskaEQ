import numpy as np
import pandas as pd
import obspy
from obspy import UTCDateTime
from pyproj import Proj
from gamma.utils import association
import subprocess
from itertools import repeat
import multiprocessing as mp


def _find_amp_sta(id, picks, window, lock, pickwamp, datadir):
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



def FindAmp(picks, datadir, window = 12, ncpu = 10):
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
        p.starmap(_find_amp_sta, zip(idl, repeat(picks), repeat(window), repeat(lock), repeat(pickwamp), repeat(datadir)))
    
    return pickwamp.df



def GenPicks(stacls, usingamp = False):
    if usingamp:
        ncpu = list(stacls.values())[0].parameters['ncpu']
        def GetPickAmp(sta):
            picksf = os.path.join(sta.workdir, 'detections', sta.name+'_outputs', "picks.csv")
            try:
                stapicks = pd.read_csv(picksf, names=["id", "timestamp", "type", "prob", "amp"])
            except FileNotFoundError:
                pass
            else:
                stapicks = FindAmp(
                    picks = stapicks, 
                    datadir = sta.datadir,
                    window = 120, 
                    ncpu = ncpu)
                with open(picksf, 'w') as fp:
                    picks.to_csv(fp, sep=",", index=False, header=False,
                        date_format='%Y-%m-%d %H:%M:%S.%f')
            return
        with mp.Pool(ncpu) as p:
            p.starmap(GetPickAmp, tqdm(stacls.values(), desc='Getting amplitudes:'))


    picks = pd.DataFrame()
    for sta in stacls.values():
        picksf = os.path.join(sta.workdir, 'detections', sta.name+'_outputs', "picks.csv")
        try:
            stapicks = pd.read_csv(picksf, names=["id", "timestamp", "type", "prob", "amp"])
        except FileNotFoundError:
            continue
        picks = picks.append(stapicks, ignore_index = True)
    picks["time_idx"] = picks["timestamp"].apply(lambda x: x.split(' ')[0])
    picks["timestamp"] = picks["timestamp"].apply(lambda x: pd.Timestamp(x))
    picks = picks.sort_values("timestamp", ignore_index=True)
    
    return picks



def GenSta(picks, stationf: str):
    station = pd.read_csv(stationf, delimiter = '|')
    stations = pd.DataFrame()

    for id in set(picks['id']):
        [nw, st, loc, cha] = id.split('.')

        if st not in list(station.Station):
            picks = picks[picks["id"] != id]
            continue

        stations = stations.append({"id": id, 
            "longitude": station[station.Station==st]["Longitude"].values[0], 
            "latitude": station[station.Station==st]["Latitude"].values[0], 
            "elevation(m)": station[station.Station==st]["Elevation"].values[0]}, ignore_index=True)
    return stations



def _association(picks, stations, config, timeList, assdir):
        picks = picks[picks['time_idx'].isin(timeList)]

        if len(picks) == 0:
            return

        picks = picks.sort_values("timestamp", ignore_index=True)
        datedir = os.path.join(assdir, timeList[0])
        if not os.path.isdir(datedir):
            os.makedirs(datedir)

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

        proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
        catalogs = pd.DataFrame(catalogs, columns=["time"]+config["dims"]+["magnitude", "sigma_time", "sigma_amp", "cov_time_amp",  "event_index", "gamma_score"])
        try:
            catalogs[["longitude","latitude"]] = catalogs.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
        except ValueError:
            print(catalogs.head())
            return
        catalogs["depth(m)"] = catalogs["z(km)"].apply(lambda x: x*1e3)
        assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
        picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
        picks = picks.merge(stations, "outer", on="id")
        picks = picks.dropna()
        
        with open(os.path.join(datedir, 'catalogs_gamma.csv'), 'w') as fp:
            catalogs.to_csv(fp, sep="\t", index=False, 
                        float_format="%.3f",
                        date_format='%Y-%m-%dT%H:%M:%S.%f')
        with open(os.path.join(datedir,'picks_gamma.csv'), 'w') as fp:
            picks.to_csv(fp, sep="\t", index=False, 
                        date_format='%Y-%m-%dT%H:%M:%S.%f')
        return



def Association(stacls):

    workdir = list(stacls.values())[0].workdir
    assdir = os.path.join(workdir, 'association')
    if not os.path.isdir(assdir):
        os.makedirs(os.path.join(assdir))
    picks = GenPicks(stacls)
    stations = GenSta(picks, os.path.join(workdir, 'station.txt'))

    config = {}
    config["center"] = (-156, 55)
    config["xlim_degree"] = [-164, -148]
    config["ylim_degree"] = [50, 60]
    config["starttime"] = UTCDateTime("20181101T00:00:00")
    config["endtime"] = UTCDateTime("20190106T00:00:00")
    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    config["dims"] = ['x(km)', 'y(km)', 'z(km)']
    xd = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
    yd = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
    config["x(km)"] = [xd[0], yd[0]]
    config["y(km)"] = [xd[1], yd[1]]
    config["z(km)"] = (0, 200)
    config["vel"] = {"p" : 6.0, "s": 6.0 / 1.75}
    config["method"] = "BGMM"
    config["oversample_factor"] = 2
    config["use_dbscan"] = True
    config["use_amplitude"] = False
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
        (0, config["z(km)"][1] + 1),  # z
        (None, None),  # t
    )
    config["dbscan_eps"] = 15
    config["dbscan_min_samples"] = 3
    config["min_picks_per_eq"] = 15
    config["max_sigma11"] = 20
    config["max_sigma22"] = 1
    config["max_sigma12"] = 1

    stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
    stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)
    starttime = pd.Timestamp(2018,11,1)
    endtime = pd.Timestamp(2019,2,1)
    
    t = starttime
    timeindex = []
    while t < endtime:
        temp = []
        for i in range(1, 5):
            temp.append(t.strftime('%Y-%m-%d'))
            t = t + pd.Timedelta(1, unit='D')
        timeindex.append(temp)

    with mp.Pool(list(stacls.values())[0].parameter['ncpu']) as p:
        p.starmap(_association, zip([picks]*len(timeindex), [stations]*len(timeindex), [config]*len(timeindex), timeindex, [assdir] * len(timeindex)))
    # for t in timeindex:
    #     _association(picks, stations, config, t, assdir)