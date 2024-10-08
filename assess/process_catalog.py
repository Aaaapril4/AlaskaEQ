import pandas as pd
import numpy as np
from math import radians, sin, cos, asin, sqrt
from double_seismic_zone.slab import Slab
from obspy import UTCDateTime
from pathlib import Path
from F1_catalog import CalFscore


def filter_catalog(cat: pd.DataFrame) -> pd.DataFrame:
    cat = cat[(cat['valid_samples']>=90)
              & (cat['depth_std_km'] <= 5)
              & (cat['longitude_std_deg'] <= 0.1)
              & (cat['latitude_std_deg'] <= 0.05)
              & (cat['time_std_s'] <= 0.7)
              & (cat["num_S"] >= 3)
              & (cat["num_P"] >= 3)
              & (cat["azimuth_gap"] < 180)]
    return cat


def calculate_accumulated(catalog: pd.DataFrame, filter_col: str, threshold: float, start: float, end: float) -> pd.DataFrame:
    catalog = catalog[~catalog[filter_col].isna()]
    catalog = catalog.reset_index(drop=True)
    catalog_overriding = catalog[catalog['slab_normal_depth_km'] <= -threshold]
    catalog_intra = catalog[catalog['slab_normal_depth_km'] >= threshold]
    catalog_slab = catalog[(catalog['slab_normal_depth_km'] < threshold) & (catalog['slab_normal_depth_km'] > -threshold)]
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


def associate(picks_det:pd.DataFrame, picks_obs:pd.DataFrame, start: UTCDateTime, end: UTCDateTime, ncpu: int = 1) -> pd.Series:
    mapper = CalFscore(picks_det, picks_obs, start, end, ncpu)
    isc_evid = cat['event_index'].apply(lambda x: mapper[x] if x in mapper else None)
    return isc_evid


if __name__ == '__main__':
    workdir = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2')
    grid = np.loadtxt('/mnt/home/jieyaqi/code/AlaskaEQ/data/slab_Fan.xyz', delimiter=',')
    start = UTCDateTime('2018-01-01')
    end = UTCDateTime('2022-12-31T23:59:59')
    
    # read catalogs
    cat = pd.read_csv(workdir / 'catalogs_bootstrap.csv')
    cat = cat[~cat['time'].isna()]
    # isc = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_catalog_reviewed.csv')
    # cmt = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/cmt.csv')
    # isc['time'] = isc['time'].apply(lambda x: UTCDateTime(x))
    cat['time'] = cat['time'].apply(lambda x: UTCDateTime(x))
    # cmt['time'] = cmt['time'].apply(lambda x: UTCDateTime(x))

    # Filter events within the region
    cat = cat[(cat['longitude'] >= -164)
              & (cat['longitude'] <= -148)
              & (cat['latitude'] >= 50)
              & (cat['latitude'] <= 60)]
    # isc = isc[(isc['longitude'] >= -164)
    #           & (isc['longitude'] <= -148)
    #           & (isc['latitude'] >= 50)
    #           & (isc['latitude'] <= 60)] 
    # isc = isc[(isc['time'] >= start) & (isc['time'] <= end) ]
    
    # read phases
    picks = pd.read_csv(workdir / 'picks_bootstrap.csv')
    picks = picks[picks['event_index'].isin(cat['event_index'])]
    picks['timestamp'] = picks['timestamp'].apply(lambda x: UTCDateTime(x))
    picks['station'] = picks['id'].apply(lambda x: x.split('.')[1])
    # isc_picks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_arrival_reviewed.csv')
    # isc_picks = isc_picks[isc_picks['station'].isin(set(picks['station']))]
    # isc_picks = isc_picks[isc_picks['event_index'].isin(isc['event_index'])]
    # isc_picks['timestamp'] = isc_picks['timestamp'].apply(lambda x: UTCDateTime(x))
    # isc_picks = isc_picks[(isc_picks['timestamp'] >= start) & (isc_picks['timestamp'] <= end)]
    
    cat = filter_catalog(cat)

    # Simeonof 2020-07-22T06:12:43.49	55.0056	-158.5615	22.5 7.8
    # Sand-point 2020-10-19T20:54:39.70	54.6127	-159.6792	32.9 7.6
    # Chignik 2021-07-29T06:15:47.49	55.4449	-157.997	22.0 8.2
    cat['time2background'] = (cat['time'] - UTCDateTime('2020-6-1')) / 60 / 60 / 24
    cat['time2simeonof'], cat['time2sandpoint'], cat['time2chignik'] = map(lambda x: determine_aftershocks(*x),
                                    [(cat, UTCDateTime('2020-07-22T06:12:43.49'), -158.5615, 55.0056, 22.5, 7.8, check_simeonof, 2),
                                     (cat, UTCDateTime('2020-10-19T20:54:39.70'), -159.6792, 54.6127, 32.9, 7.6, check_sandpoint, 2),
                                     (cat, UTCDateTime('2021-07-29T06:15:47.49'), -157.997, 55.4449, 22.0, 8.2, check_chignik, 1)])
                                                                            
    # cat['isc_id'] = associate(picks, isc_picks, start, end, 20)
    # temp_cat = cat.merge(cmt, left_on='isc_id', right_on='eventid', how = 'left', suffixes = ('', '_isc'))
    # cat = temp_cat.drop(labels=['longitude_isc', 'latitude_isc', 'depth_isc', 'event_index_isc', 'eventid', 'time_isc', 'timer_2018', 'timer_2020', 'timer_simeonof', 'timer_sandpoint', 'timer_chignik'], axis = 1)

    slab_alaska = Slab(grid, [-166, -148, 50, 60])
    slab_alaska.transform()
    slab_alaska.interp(0.1)
    slab_alaska.init_tree()

    cat['slab_normal_depth_km'] = cat.apply(lambda x: slab_alaska.get_distance([x["longitude"], x["latitude"], x["depth_km"]]), axis = 1)

    event_num = calculate_accumulated(cat, 'time2sandpoint', 5, -200, 600)
    event_num.to_csv(workdir / 'sandpoint_200', index=False)
    event_num = calculate_accumulated(cat, 'time2chignik', 5, -20, 60)
    event_num.to_csv(workdir / 'chignik_20', index=False)
    event_num = calculate_accumulated(cat, 'time2simeonof', 5, -20, 60)
    event_num.to_csv(workdir / 'simeonof_20', index=False)

    cat.to_csv(workdir / 'catalogs_bootstrap_processed.csv', index=False)
    picks = picks[picks['event_index'].isin(cat['event_index'])]
    picks.to_csv(workdir / 'picks_bootstrap_processed.csv', index=False)