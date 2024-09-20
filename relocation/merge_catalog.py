import pandas as pd
import numpy as np
from obspy import UTCDateTime
from pathlib import Path
from reloc2df import reloc_to_df

def std_ref_to_all(data: pd.DataFrame, avg: pd.Series):
    data = data.sub(avg, axis = 0)
    data = data ** 2
    std = data.mean(axis = 1).pow(1/2)
    return std


workdir = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2')
cat = reloc_to_df(Path / "bootstrap" / "iter0" / "output" / "tomoFDD.reloc")
for i in range(1, 100+1):
    cat_rel = reloc_to_df(Path / "bootstrap" / f'iter{i}' / "output" / "tomoFDD.reloc")
    if len(cat_rel) == 0:
        print("No data for iteration ", i)
        continue

    cat = cat.merge(cat_rel, on = 'event_index', how='outer', suffixes=('', f'_iter{i}'))

cat = cat[~cat['latitude'].isna()]
cat['valid'] = cat[[col for col in cat.columns if 'timer_iter' in col]].count(axis = 1)
cat['latitude_std'] = std_ref_to_all(cat[[col for col in cat.columns if 'latitude_iter' in col]], cat['latitude'])
cat['longitude_std'] = std_ref_to_all(cat[[col for col in cat.columns if 'longitude_iter' in col]], cat['longitude'])
cat['depth_std'] = std_ref_to_all(cat[[col for col in cat.columns if 'depth_iter' in col]], cat['depth'])
cat['time_std'] = std_ref_to_all(cat[[col for col in cat.columns if 'timer_iter' in col]], cat['timer'])
cat.to_csv(Path / 'catalogs_bootstrap.csv', 
           index = False,
           columns=['event_index', 'longitude', 'latitude', 'depth', 'time', 'longitude_std', 'latitude_std',
                    'depth_std', 'time_std', 'valid'])