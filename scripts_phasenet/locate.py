import numpy as np
from gamma.seismic_ops import initialize_eikonal, calc_loc, calc_time, huber_loss_grad
import pandas as pd
from pyproj import Proj
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import multiprocessing as mp
from functools import partial

def convert_picks_csv(picks, stations, config):
    # t = picks["timestamp"].apply(lambda x: x.timestamp()).to_numpy()
    if type(picks["timestamp"].iloc[0]) is str:
        picks.loc[:,"timestamp"] = picks["timestamp"].apply(lambda x: datetime.fromisoformat(x))
    t = (
        picks["timestamp"]
        .apply(lambda x: x.tz_convert("UTC").timestamp() if x.tzinfo is not None else x.tz_localize("UTC").timestamp())
        .to_numpy()
    )
    # t = picks["timestamp"].apply(lambda x: x.timestamp()).to_numpy()
    timestamp0 = np.min(t)
    t = t - timestamp0
    if config["use_amplitude"]:
        a = picks["amp"].apply(lambda x: np.log10(x * 1e2)).to_numpy()  ##cm/s
        data = np.stack([t, a]).T
    else:
        data = t[:, np.newaxis]
    meta = stations.merge(picks["id"], how="right", on="id")
    locs = meta[config["dims"]].to_numpy()
    phase_type = picks["type"].apply(lambda x: x.lower()).to_numpy()
    phase_weight = picks["prob"].to_numpy()[:, np.newaxis]
    pick_idx = picks['pick_idx'].to_numpy()
    pick_station_id = picks.apply(lambda x: x.id + "_" + x.type, axis=1).to_numpy()
    nan_idx = meta.isnull().any(axis=1)
    return (
        data[~nan_idx],
        locs[~nan_idx],
        phase_type[~nan_idx],
        phase_weight[~nan_idx],
        pick_idx[~nan_idx],
        pick_station_id[~nan_idx],
        timestamp0,
    )

def get_config() -> dict:
    '''
    Configuration for GaMMA
    '''
    config = {}
    config['initial_points'] = [1, 1, 2] # x, y, depth
    config["center"] = (-156, 55)
    config["xlim_degree"] = [-166, -146] # 1 or 2 degrees larger
    config["ylim_degree"] = [48, 62]
    config["z(km)"] = (0, 400)
    config["covariance_prior"] = [300, 300]
    config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
    config["method"] = "BGMM"
    config["oversample_factor"] = 30 #70 for without XO, 30 for XO
    config["use_dbscan"] = True
    config["use_amplitude"] = False
    config["dbscan_eps"] = 30 # 70 for without XO, 30 for XO
    config["dbscan_min_samples"] = 6
    config["min_picks_per_eq"] = 6
    config["min_p_picks_per_eq"] = 0
    config["min_s_picks_per_eq"] = 0
    config["max_sigma11"] = 2
    config["max_sigma22"] = 2
    config["max_sigma12"] = 2
    config["ncpu"] = 40

    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    config["dims"] = ['x(km)', 'y(km)', 'z(km)']
    lt = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
    lb = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
    rt = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
    rb = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
    config["x(km)"] = [min(lt[0], lb[0]), max(rt[0], rb[0])]
    config["y(km)"] = [min(lb[1], rb[1]), max(lt[1], rt[1])]
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
        (0, config["z(km)"][1] + 1),  # x
        (None, None),  # t
        )

    # uncomment if you choose to use 1D velocity model
    # Alaska model (averaged from Fan Wang's model)
    d, Vp, Vs = np.loadtxt("/mnt/home/jieyaqi/code/AlaskaEQ/data/alaska.csv", usecols=(0, 1, 2), unpack=True, skiprows=1, delimiter=',')
    # PREM model
    # d, Vpv, Vph, Vsv, Vsh = np.loadtxt("PREM.csv", usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1)
    # Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
    # Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)
    config["eikonal"] = {"xlim": config["x(km)"], 
                        "ylim": config["y(km)"], 
                        "zlim": config["z(km)"], 
                        "h": 1,
                        "vel": {"p": Vp, "s": Vs, "z": d}}
    return config, proj

def check_event(p_num, s_num, config):
    if p_num >= 10:
        return True
    if p_num >= config['min_p_picks_per_eq'] and s_num >= config['min_s_picks_per_eq'] and p_num + s_num >= config['min_picks_per_eq']:
        return True
    return False

def locate(picks, stations, config, proj, max_iter=100):
    phase_time, station_loc, phase_type, weight, pick_idx, pick_station_id, timestamp0 = convert_picks_csv(
        picks, stations, config
    )
    n_data = phase_time.shape[0]
    n_sample = (max(int(n_data * 0.7), 4))
    best_loc, best_loss, best_mask= [0, 0, 20, 0], np.inf, None
    for _ in range(max_iter):
        mask = np.random.choice(n_data, n_sample, replace=False)
        est_loc = calc_loc(phase_time[mask], phase_type[mask], station_loc[mask], weight[mask], [0, 0, 20, 0], config["eikonal"], config["vel"], config["bfgs_bounds"])[0]
        predict_time = calc_time(est_loc, station_loc, phase_type, config["vel"], config['eikonal'])
        inlier = np.squeeze(abs(phase_time - predict_time) <= 2)
        loss = huber_loss_grad(np.squeeze(est_loc), phase_time[inlier], phase_type[inlier], station_loc[inlier], weight[inlier], config['vel'], 1, config['eikonal'])[0]
        if loss < best_loss:
            best_loss = loss
            best_loc = est_loc[0]
            best_mask = np.squeeze(abs(phase_time - predict_time) <= 5)

    best_loc = calc_loc(phase_time[best_mask], phase_type[best_mask], station_loc[best_mask], weight[best_mask], [0, 0, 20, 0], config["eikonal"], config["vel"], config["bfgs_bounds"])[0][0]
    
    phase_type = phase_type[best_mask]
    p_num, s_num = np.sum(phase_type == 'p'), np.sum(phase_type == 's')
    if not check_event(p_num, s_num, config):
        return None, None, None, None

    picks_used_idx = pick_idx[best_mask]
    
    evlon, evlat = proj(longitude=best_loc[0], latitude=best_loc[1], inverse=True)
    evtime = pd.to_datetime(timestamp0 + best_loc[3], unit='s')
    
    return [evlon, evlat, best_loc[2], evtime], picks[picks['pick_idx'].isin(picks_used_idx)], p_num, s_num

def process_single_event(evid, picks, stations, config, proj):
    """
    Process a single event for parallel execution
    """
    try:
        estloc, phase, p_num, s_num = locate(picks[picks['event_index'] == evid], stations, config, proj)
        if estloc:
            return {
                'event_index': evid,
                'longitude': estloc[0],
                'latitude': estloc[1], 
                'depth(m)': estloc[2] * 1000,
                'time': estloc[3],
                'num_picks': p_num + s_num,
                'num_p_picks': p_num,
                'num_s_picks': s_num
            }, phase.drop(columns=['pick_idx'])
        else:
            return None, None
    except Exception as e:
        print(f"Error processing event {evid}: {e}")
        return None, None

workdir = Path('/mnt/scratch/jieyaqi/alaska/alaska_long')

config, proj = get_config()
config["eikonal"] = initialize_eikonal(config["eikonal"])

# set up stations
stations = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/stations.csv')
stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)

picks = pd.read_csv(workdir / 'picks_gamma.csv')

# set up events
events = pd.read_csv(workdir / 'catalogs_gamma.csv')
events = events[
    ((events['num_picks'] >= 10) & (events['num_s_picks'] >= 3) & (events['num_p_picks'] >= 3)) |
    (events['num_p_picks'] >= 10)
    ]

# Add pick_idx to picks for tracking
picks['pick_idx'] = picks.index

# Get list of event IDs to process
event_ids = events['event_index'].tolist()
# event_ids = [251213]

# Set up multiprocessing
ncpu = config["ncpu"]  # Use the CPU count from config
print(f"Processing {len(event_ids)} events using {ncpu} CPUs")

# Create partial function with fixed arguments
process_func = partial(process_single_event, picks=picks, stations=stations, config=config, proj=proj)

# Process events in parallel
event_locate = []
picks_locate = []

with mp.Pool(processes=ncpu) as pool:
    # Use imap for better memory management and progress tracking
    results = list(tqdm(
        pool.imap(process_func, event_ids, chunksize=max(1, len(event_ids) // (ncpu * 4))),
        total=len(event_ids),
        desc="Processing events"
    ))

# Collect results
for event_data, picks_data in results:
    if event_data is not None:
        event_locate.append(event_data)
        picks_locate.append(picks_data)

# Convert to DataFrames
if event_locate:
    event_locate = pd.DataFrame(event_locate, columns=events.columns)
    picks_locate = pd.concat(picks_locate, ignore_index=True)
else:
    event_locate = pd.DataFrame(columns=events.columns)
    picks_locate = pd.DataFrame(columns=picks.columns)

print(f"Successfully processed {len(event_locate)} events")

picks_locate.to_csv(workdir / 'picks_locate.csv', index=False)
event_locate.to_csv(workdir / 'catalogs_locate.csv', index=False)