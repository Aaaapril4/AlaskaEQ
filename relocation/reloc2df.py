import pandas as pd
import numpy as np
from obspy import UTCDateTime
from pathlib import Path

otime = UTCDateTime(1970, 1, 1)
def reloc_to_df(relocf):

    try:      
        index, lat, lon, dep, yr, mon, day, hr, min, sec = np.loadtxt(relocf, unpack=True, usecols=(0,1,2,3, 10, 11, 12, 13, 14, 15))
    except:
        return pd.DataFrame()
    
    cat_rel = pd.DataFrame()
    cat_rel['event_index'] = index.astype(int)
    cat_rel[f'latitude'] = lat
    cat_rel[f'longitude'] = lon
    cat_rel[f'depth'] = dep
    cat_rel[f'time'] = pd.NA
    for i in range(len(index)):
        iyr, imon, iday, ihr, imin, isec = int(yr[i]), int(mon[i]), int(day[i]), int(hr[i]), int(min[i]), int(sec[i])
        imsec = int(sec[i] % 1 * 1e6)
        if isec >= 60:
            isec -= 1
            imsec = 99999
        try:
            cat_rel.loc[i, f'time'] = UTCDateTime(iyr, imon, iday, ihr, imin, isec, imsec)
        except:
            pass
    cat_rel[f'timer'] = cat_rel[f'time'] - otime
    return cat_rel

workdir = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1')
relocf = workdir / "relocation" / "output" / "tomoFDD.reloc"
phase = pd.read_csv(workdir / "picks_gamma.csv")

cat = reloc_to_df(relocf)
phase = phase[phase['event_index'].isin(cat['event_index'])]
cat.to_csv(workdir / "catalogs_tomodd.csv", index=False, columns=['event_index', 'longitude', 'latitude', 'depth', 'time'])
phase.to_csv(workdir / "picks_tomodd.csv", index=False)