import pandas as pd
import numpy as np
from math import radians, sin, cos, asin, sqrt
from double_seismic_zone.slab import Slab
from obspy import UTCDateTime
from pathlib import Path
from F1_catalog import CalFscore

def calculate_phase_num(eventid: int, pick: pd.DataFrame) -> tuple[int, int, int]:
    evphase = pick[pick['event_index'] == eventid]
    return len(evphase[evphase['type']=='P']), len(evphase[evphase['type']=='S'])


def calculate_horizontal_std(cat: pd.DataFrame) -> pd.DataFrame:
    dist_lat = lambda x: (6371 * np.cos(x / 180 * np.pi) * 2 * np.pi) / 360
    cat['horizontal_std'] = cat.apply(lambda x: np.sqrt((x['longitude_std']*dist_lat(0))**2 + (x['latitude_std']*dist_lat(x['latitude']))**2), axis = 1)
    return cat


def filter_catalog(cat: pd.DataFrame) -> pd.DataFrame:
    cat = cat[(cat['valid']>=90)
              & (cat['depth_std'] <= 5)
              & (cat['longitude_std'] <= 0.1)
              & (cat['latitude_std'] <= 0.05)
              & (cat['time_std'] <= 0.7)
              & (cat["num_phase"] >= 10)
              & (cat["num_S"] >= 3)
              & (cat["num_P"] >= 3)]
    return cat


def calculate_accumulated(catalog: pd.DataFrame, filter_col: str, threshold: float, start: float, end: float) -> pd.DataFrame:
    catalog = catalog[~catalog[filter_col].isna()]
    catalog = catalog.reset_index(drop=True)
    catalog_overriding = catalog[catalog['slab_normal_depth'] <= -threshold]
    catalog_intra = catalog[catalog['slab_normal_depth'] >= threshold]
    catalog_slab = catalog[(catalog['slab_normal_depth'] < threshold) & (catalog['slab_normal_depth'] > -threshold)]
    catalog_slab = catalog_slab.reset_index(drop=True)
    catalog_intra = catalog_intra.reset_index(drop=True)
    catalog_overriding = catalog_overriding.reset_index(drop=True)

    d = start
    time = []
    num_overriding = []
    num_intra = []
    num_slab = []

    while d <= end:
        time.append(d)
        num_intra.append(len(catalog_intra[
            (catalog_intra[filter_col] >= d)
            & (catalog_intra[filter_col] < d+1)
        ]))
        num_overriding.append(len(catalog_overriding[
            (catalog_overriding[filter_col] >= d)
            & (catalog_overriding[filter_col] < d+1)
        ]))
        num_slab.append(len(catalog_slab[
            (catalog_slab[filter_col] >= d)
            & (catalog_slab[filter_col] < d+1)
        ]))
        d += 1

    event_num = pd.DataFrame({'timer': time, 
                          'num_overriding': num_overriding, 
                          'num_slab': num_slab,
                          'num_intra': num_intra})
    event_num['accum_overriding'] = event_num['num_overriding'].cumsum()
    event_num['accum_slab'] = event_num['num_slab'].cumsum()
    event_num['accum_intra'] = event_num['num_intra'].cumsum()
    return event_num


def check_sandpoint(lon: float, lat: float) -> bool:
    if lat > 54 and lon <= -160.2:
        return False
    if lat > 54 and lon >= -159.3:
        return False
    if lat > 54.8:
        return False
    return True


def check_chignik(lon: float, lat: float) -> bool:
    if lon <= -159:
        return False
    if lat >= 56.15:
        return False
    return True


def check_simeonof(lon: float, lat: float) -> bool:
    if lon <= -161.3:
        return False
    if lat >= 55.5:
        return False
    return True


def great_circle(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    '''
    Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    '''
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def determine_aftershocks(cat: pd.DataFrame, evtime: UTCDateTime, evlon: float, evlat: float, evdep: float, evmag: float, check, factor) -> pd.Series:
    fault_length = 10**(-2.9 + 0.63 * evmag) * factor
    def check_event(time, lon, lat):
        if (great_circle(lon, lat, evlon, evlat) <= fault_length) and check(lon, lat):
            return (time - evtime) / 60 / 60 / 24
        return 

    time = cat.apply(lambda x: check_event(x['time'], x['longitude'], x['latitude']), axis = 1)
    return time


def associate(picks_obs:pd.DataFrame, picks_det:pd.DataFrame, start: UTCDateTime, end: UTCDateTime) -> pd.Series:
    mapper = CalFscore(picks_det, picks_obs, start, end)
    mapper_reverse = {}
    for k, v in mapper.itmes():
        mapper_reverse[v] = k
    isc_evid = cat['event_index'].apply(lambda x: mapper_reverse[x] if x in mapper_reverse else None)
    return isc_evid


if __name__ == '__main__':
    workdir = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2')
    grid = np.loadtxt('/mnt/home/jieyaqi/code/AlaskaEQ/data/slab_Fan.xyz', delimiter=',')
    start = UTCDateTime('2018-01-01')
    end = UTCDateTime('2022-12-31T23:59:59')
    
    # read catalogs
    cat = pd.read_csv(workdir / 'catalogs_tomodd.csv')
    cat = cat[~cat['time'].isna()]
    isc = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_catalog.csv')
    cmt = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt.csv')
    isc['time'] = isc['time'].apply(lambda x: UTCDateTime(x))
    cat['time'] = cat['time'].apply(lambda x: UTCDateTime(x))
    cmt['time'] = cmt['time'].apply(lambda x: UTCDateTime(x))

    # Filter events within the region
    cat = cat[(cat['longitude'] >= -164)
              & (cat['longitude'] <= -148)
              & (cat['latitude'] >= 50)
              & (cat['latitude'] <= 60)]
    
    # read phases
    picks = pd.read_csv(workdir / 'picks_tomodd.csv')
    picks = picks[picks['event_index'].isin(cat['event_index'])]
    picks['timestamp'] = picks['timestamp'].apply(lambda x: UTCDateTime(x))
    picks['station'] = picks['id'].apply(lambda x: x.split('.')[1])
    isc_picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_arrival.csv')
    isc_picks = isc_picks[isc_picks['station'].isin(set(picks['station']))]
    isc_picks = isc_picks[isc_picks['event_index'].isin(isc['event_index'])]
    isc_picks['timestamp'] = isc_picks['timestamp'].apply(lambda x: UTCDateTime(x))
    isc_picks = isc_picks[(isc_picks['timestamp'] > start) & (isc_picks['timestamp'] <= end)]
    
    # fit the bootstrap result
    cat['longitude_std'] = 0.03
    cat['latitude_std'] = 0.03
    cat['depth_std'] = 3
    cat['time_std'] = 0.1
    cat['valid'] = 100

    cat['num_P'], cat['num_S'] = zip(*cat['event_index'].apply(lambda x: calculate_phase_num(x, picks)))
    # cat = filter_catalog(cat)
    cat = calculate_horizontal_std(cat)

    # Simeonof 2020-07-22T06:12:43.49	55.0056	-158.5615	22.5 7.8
    # Sand-point 2020-10-19T20:54:39.70	54.6127	-159.6792	32.9 7.6
    # Chignik 2021-07-29T06:15:47.49	55.4449	-157.997	22.0 8.2
    cat['time2background'] = cat['time'] - UTCDateTime('2020-6-1')
    cat['time2simeonof'], cat['time2sandpoint'], cat['time2chignik'] = map(lambda x: determine_aftershocks(*x),
                                    [(cat, UTCDateTime('2020-07-22T06:12:43.49'), -158.5615, 55.0056, 22.5, 7.8, check_simeonof, 2),
                                     (cat, UTCDateTime('2020-10-19T20:54:39.70'), -159.6792, 54.6127, 32.9, 7.6, check_sandpoint, 2),
                                     (cat, UTCDateTime('2021-07-29T06:15:47.49'), -157.997, 55.4449, 22.0, 8.2, check_chignik, 1)])
                                                                            
    cat['isc_id'] = associate(isc_picks, picks, start, end)
    temp_cat = cat.merge(cmt, left_on='isc_id', right_on='event_id', how = 'left')
    temp_cat.drop(labels=['longitude','latitude','depth','event_index','eventid','time','timer_2018','timer_2020','timer_simeonof','timer_sandpoint','timer_chignik'], inplace=True)
    cat = temp_cat

    slab_alaska = Slab(grid, [-166, -148, 50, 60])
    slab_alaska.transform()
    slab_alaska.interp(0.1)
    slab_alaska.init_tree()

    cat['slab_normal_depth'] = cat.apply(lambda x: slab_alaska.get_distance([x["longitude"], x["latitude"], x["depth"]]), axis = 1)

    event_num = calculate_accumulated(cat, 'timer_sandpoint', 5, -200, 600)
    event_num.to_csv(workdir / 'sandpoint_200_new', index=False)
    event_num = calculate_accumulated(cat, 'timer_chignik', 5, -20, 60)
    event_num.to_csv(workdir / 'chignik_20_new', index=False)
    event_num = calculate_accumulated(cat, 'timer_simeonof', 5, -20, 60)
    event_num.to_csv(workdir / 'simeinof_20_new', index=False)
    # cat = cat[cat['valid']>=60]
    # cat = cat[cat['depth_std'] < 10]
    # cat = cat[cat['longitude_std'] < 0.1]
    # cat = cat[cat['latitude_std'] < 0.1]
    # cat = cat[cat['time_std'] < 1]
    # cat['time'] = cat['time'].apply(lambda x: UTCDateTime(x))
    # cat['time_relative_2018'] = (cat['time'] - UTCDateTime(2018, 1, 1))/60/60/24
    # cat['time_relative_2020'] = (cat['time'] - UTCDateTime(2020, 1, 1))/60/60/24

    cat.to_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all/catalog_bootstrap_40_1_associated.csv', index=False)