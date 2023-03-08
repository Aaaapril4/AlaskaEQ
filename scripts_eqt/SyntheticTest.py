import pandas as pd
from pyproj import Proj
from obspy import UTCDateTime
import numpy as np
import random
from gamma.utils import association


picks = pd.read_csv('data/ManualPickswamp.csv', delimiter = '\t')
picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x))
picks = picks[picks['timestamp'] > pd.Timestamp(2018, 7, 3)]
picks = picks[picks['timestamp'] < pd.Timestamp(2018, 7, 4)]
event = pd.read_csv('data/events.csv', delimiter='\t')
stations = pd.read_csv('data/stations.csv', delimiter = '\t')
event['time'] = event['time'].apply(lambda x: pd.Timestamp(x[:-1]))

up = np.loadtxt("workflow/up.csv")
us = np.loadtxt("workflow/us.csv")
d, Vpv, Vph, Vsv, Vsh = np.loadtxt('workflow/PREM.csv', usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1)
Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)

picks = picks.sort_values("timestamp", ignore_index = True)
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
config["vel"] = {"p": 6, "s": 6/1.73}
# config["vel"] = {"p": Vp, "s": Vs, "depth": d}
# config["eikonal"] = {"up": up, "us": us}
# config["eikonal_grid"] = 1
config["vel"] = {"p": Vp, "s": Vs, "z": d}
config["eikonal"] = {"xlim": config["x(km)"], 
                     "ylim": config["y(km)"], 
                     "zlim": config["z(km)"], 
                     "h": 1,
                     "vel": config["vel"]}
config["covariance_prior"] = [30, 30] #[20,20]
config["method"] = "BGMM"
config["oversample_factor"] = 15 #15
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
config["min_picks_per_eq"] = 0
config["max_sigma11"] = 1000
config["max_sigma22"] = 1000
config["max_sigma12"] = 1000

stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)


num = 8
t0 = pd.Timestamp(2018, 7, 3, 0)
t1 = pd.Timestamp(2018, 7, 3, 0, 10)
eventl = random.sample(list(set(picks.evid)), num)
timel = random.choices(range((t1 - t0).seconds), k=num)
picks_syn = pd.DataFrame()
event_syn = pd.DataFrame()
for i in range(num):
    eventid = eventl[i]
    event_tmp = event[event["evid"]==eventid]
    delta = pd.Timedelta((pd.Timestamp(event_tmp['time'].values[0])-t0).seconds-timel[i], 's')
    event_tmp['time'] = event_tmp['time'].apply(lambda x: x - delta)
    event_syn = pd.concat([event_syn, event_tmp])
    picks_tmp = picks[picks['evid']==eventid]
    picks_tmp['timestamp'] = picks_tmp['timestamp'].apply(lambda x: x - delta)
    picks_syn = pd.concat([picks_syn, picks_tmp])

# picks_syn = pd.read_csv('picks_syn.csv', delimiter = '\t')
# event = pd.read_csv('event_syn.csv', delimiter='\t')

pickst = picks_syn #[['id', 'evid', 'timestamp', 'type', 'time_idx', 'prob', 'amp']]
event_idx0 = 0  ## current earthquake index
assignments = []
catalogs, assignments = association(
    pickst, 
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
pickst = pickst.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
pickst = pickst.merge(stations, "outer", on="id")
pickst = pickst.dropna()
with open('catalogs_syn.csv', 'w') as fp:
    catalogs.to_csv(fp, sep="\t", index=False, 
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')
with open('picks_syn.csv', 'w') as fp:
    pickst.to_csv(fp, sep="\t", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')
with open('event_syn.csv', 'w') as fp:
    event_syn.to_csv(fp, sep="\t", index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')