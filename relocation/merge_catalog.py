import pandas as pd
import numpy as np
import obspy
from pathlib import Path
from reloc2df import reloc_to_df


def std_ref_to_all(data: pd.DataFrame, avg: pd.Series):
    data = data.sub(avg, axis = 0)
    data = data ** 2
    std = data.mean(axis = 1).pow(1/2)
    return std


def calculate_phase_num(eventid: int, pick: pd.DataFrame) -> tuple[int, int, int]:
    evphase = pick[pick['event_index'] == eventid]
    return len(evphase[evphase['type']=='P']), len(evphase[evphase['type']=='S'])


def calculate_azimuth_gap(eventid: int, evlon: float, evlat: float, pick: pd.DataFrame) -> float:
    evphase = pick[pick['event_index'] == eventid]
    evphase = evphase.drop_duplicates(subset='id')
    evphase['azimuth'] = evphase.apply(lambda x:
        obspy.geodetics.base.gps2dist_azimuth(evlat, evlon, x['latitude'], x['longitude'])[1], axis = 1)
    azimuth = evphase['azimuth'].to_numpy()
    azimuth.sort()
    gap = np.append(azimuth[1:] - azimuth[:-1], 360 - azimuth[-1] + azimuth[0])
    return gap.max()


workdir = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2')
picks = pd.read_csv(workdir / 'picks_gamma.csv')
cat = reloc_to_df(workdir / "bootstrap" / "iter0" / "output" / "tomoFDD.reloc")
for i in range(1, 100+1):
    print(f'processing iter {i}')
    cat_rel = reloc_to_df(workdir / "bootstrap" / f'iter{i}' / "output" / "tomoFDD.reloc")
    if len(cat_rel) == 0:
        print("No data for iteration ", i)
        continue

    cat = cat.merge(cat_rel, on = 'event_index', how='left', suffixes=('', f'_iter{i}'))

cat = cat[~cat['time'].isna()]
cat['valid_samples'] = cat[[col for col in cat.columns if 'timer_iter' in col]].count(axis = 1)
cat['longitude_std_deg'] = std_ref_to_all(cat[[col for col in cat.columns if 'longitude_iter' in col]], cat['longitude'])
cat['latitude_std_deg'] = std_ref_to_all(cat[[col for col in cat.columns if 'latitude_iter' in col]], cat['latitude'])
dist_lat = lambda x: (6371 * np.cos(x / 180 * np.pi) * 2 * np.pi) / 360
cat['horizontal_std_km'] = cat.apply(lambda x: np.sqrt((x['longitude_std_deg']*dist_lat(0))**2 + (x['latitude_std_deg']*dist_lat(x['latitude']))**2), axis = 1)
cat['depth_std_km'] = std_ref_to_all(cat[[col for col in cat.columns if 'depth_km_iter' in col]], cat['depth_km'])
cat['time_std_s'] = std_ref_to_all(cat[[col for col in cat.columns if 'timer_iter' in col]], cat['timer'])
cat['num_P'], cat['num_S'] = zip(*cat['event_index'].apply(lambda x: calculate_phase_num(x, picks)))
cat['azimuth_gap'] = cat.apply(lambda x: calculate_azimuth_gap(x["event_index"], x["longitude"], x["latitude"], picks), axis = 1)

cat.to_csv(workdir / 'catalogs_bootstrap.csv', 
           index = False,
           columns=['event_index', 'longitude', 'latitude', 'depth_km', 'time', 'longitude_std_deg', 'latitude_std_deg', 'horizontal_std_km', 'depth_std_km', 'time_std_s', 'valid_samples', 'num_P', 'num_S', 'azimuth_gap'])
picks = picks[picks['event_index'].isin(cat['event_index'])]
picks.to_csv(workdir / 'picks_bootstrap.csv', index=False)