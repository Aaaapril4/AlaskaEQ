import pandas as pd
import swifter
from math import radians, sin, cos, asin, sqrt

picks = pd.read_csv('/mnt/scratch/jieyaqi/alaska/alaska_long/picks_gamma_10.csv')
picks['timestamp'] = picks['timestamp'].swifter.apply(lambda x: pd.to_datetime(x))
cat = pd.read_csv('/mnt/scratch/jieyaqi/alaska/alaska_long/catalogs_new_10.csv')
# cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/catalogs_gamma.csv')


def calculate_accumulated(catalog: pd.DataFrame, filter_col: str, threshold: float, start: float, end: float, width: float, window: int, eventtime: pd.Timestamp, name: str) -> pd.DataFrame:
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
    num_station = []

    while d <= end:
        time.append(d)
        cat_day = catalog[(catalog[filter_col] >= d)
            & (catalog[filter_col] < d+width)]
        pick_day = picks[picks['event_index'].isin(cat_day['event_index'])]
        num_station.append(len(set(pick_day['id'])))
        num_intra.append(len(catalog_intra[
            (catalog_intra[filter_col] >= d)
            & (catalog_intra[filter_col] < d+width)
        ]))
        num_overriding.append(len(catalog_overriding[
            (catalog_overriding[filter_col] >= d)
            & (catalog_overriding[filter_col] < d+width)
        ]))
        num_slab.append(len(catalog_slab[
            (catalog_slab[filter_col] >= d)
            & (catalog_slab[filter_col] < d+width)
        ]))
        d += width

    event_num = pd.DataFrame({'timer': time, 
                          'num_overriding': num_overriding, 
                          'num_slab': num_slab,
                          'num_intra': num_intra,
                          'num_station': num_station})
    event_num['accum_overriding'] = event_num['num_overriding'].cumsum()
    event_num['accum_slab'] = event_num['num_slab'].cumsum()
    event_num['accum_intra'] = event_num['num_intra'].cumsum()
    event_num["num_overriding_MA"] = (event_num["num_overriding"] / event_num["num_station"]).rolling(window=window, min_periods=2).mean()
    event_num["num_slab_MA"] = (event_num["num_slab"] / event_num["num_station"]).rolling(window=window, min_periods=2).mean()
    event_num["num_intra_MA"] = (event_num["num_intra"] / event_num["num_station"]).rolling(window=window, min_periods=2).mean()
    event_num.to_csv(name, index=False)
    return event_num


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


def volcano_catalog(cat: pd.DataFrame, lon_vol: float, lat_vol: float, width: float):
    dist2volcano = cat.swifter.apply(lambda x: great_circle(x['longitude'], x['latitude'], lon_vol, lat_vol), axis = 1)
    return cat[dist2volcano <= width]


def calculate_accumulated_volcano(catalog: pd.DataFrame, lon_vol: float, lat_vol: float, start: float, width: float, barwidth: float, window: int, name: str) -> pd.DataFrame:
    catalog = volcano_catalog(cat, lon_vol, lat_vol, width)
    catalog = catalog.reset_index(drop=True)

    d = start
    time = []
    num = []
    num_station = []

    while d <= 0:
        time.append(d)
        cat_day = catalog[(catalog['delta_time'] >= d)
            & (catalog['delta_time'] < d+barwidth)]
        pick_day = picks[picks['event_index'].isin(cat_day['event_index'])]
        num_station.append(len(set(pick_day['id'])))
        num.append(len(cat_day))
        d += barwidth

    event_num = pd.DataFrame({'timer': time, 
                          'num': num, 
                          'num_station': num_station})
    event_num['accum_num'] = event_num['num'].cumsum()
    event_num["num_MA"] = (event_num["num"] / event_num["num_station"]).rolling(window=window, min_periods=1).mean()
    event_num.to_csv(name, index=False)
    return event_num


# calculate for main events
# event_num_simeonof, event_num_chignik, event_num_sandpoint, event_num_sandpoint2023, num_control = map(lambda x: calculate_accumulated(*x),
#     [(cat, 'time2simeonof', 1000, -9600, 500, 7, 10, pd.to_datetime('2020-07-22T06:12:43.49'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/simeonof.csv'),
#      (cat, 'time2chignik', 1000, -9600, 500, 7, 10, pd.to_datetime('2021-07-29T06:15:47.49'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/chignik.csv'),
#      (cat[cat['latitude'] > 53.8], 'time2sandpoint', 1000, -9600, 500, 7, 10, pd.to_datetime('2020-10-19T20:54:39.70'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint.csv'),
#      (cat, 'time2sandpoint2023', 1000, -9600, 500, 7, 10, pd.to_datetime('2023-07-16T06:48:21.158'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint2023.csv'),
#      (cat, 'time2control', 1000, -9600, 0, 7, 10, pd.to_datetime('2024-01-01'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/control.csv')])

# calculate_accumulated(cat, 'time2sandpoint2023', 5, -5, 30, 1, 90, pd.to_datetime('2023-07-16T06:48:21.158'), '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/sandpoint2023_zoomin.csv')
calculate_accumulated_volcano(cat, -155.1026, 58.2343, -9600, 1.4 * 1.2, 7, 10, '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/trident.csv')
# # calculate for volcanos
# event_num_pavlof, event_num_veniaminof, event_num_aniakchak, 
# event_num_trident = map(lambda x: calculate_accumulated_volcano(*x),
# #     [(cat, -161.8937, 55.4173, -9600, 25, 90, '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/pavlof.csv'),
# #      (cat, -159.3931, 56.1979, -9600, 25, 90, '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/veniaminof.csv'),
# #      (cat, -158.209, 56.9058, -9600, 25, 90, '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/aniakchak.csv'),
#      [(cat, -155.1026, 58.2343, -9600, 1.4 * 1.2, 7, 10, '/mnt/ufs18/nodr/home/jieyaqi/alaska/Alaska_long/trident.csv')])