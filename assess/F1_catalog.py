import pandas as pd
from collections import defaultdict
from obspy import UTCDateTime
from string import Template
import swifter
from F1_picks import CalFscore as PickFscore

F1_template = Template("F1 for $type\n \
    precision: $precision\n \
    recall: $recall\n \
    f1: $f1\n \
    tp: $tp\n \
    fp: $fp\n \
    fn: $fn")

def map_events(picks_TP: pd.DataFrame, 
               event_obs_pool:pd.DataFrame, 
               event_det_pool:pd.DataFrame):
    event_det_pool = event_det_pool.difference([-1])

    counter=defaultdict(int)
    def count_func(row):
        if row.event_index!=-1:
            counter[(row.evid_obs,row.event_index)]+=1

    picks_TP.apply(count_func,axis=1)
    status=[]
    for key in counter:
        status.append([counter[key],key[0],key[1]])
    status.sort(reverse=True)

    mapper={}
    for _,evid_obs,event_index in status:
        if evid_obs in event_obs_pool and event_index in event_det_pool:
            mapper[event_index]=evid_obs
            event_obs_pool.remove(evid_obs) 
            event_det_pool.remove(event_index)
    return mapper, event_obs_pool, event_det_pool


def CalFscore(picks_det: pd.DataFrame, picks_obs: pd.DataFrame, start: UTCDateTime, end: UTCDateTime, ncpu: int = 1):
    
    picks_TP, picks_FN, picks_FP = PickFscore(picks_det, picks_obs, start, end, ncpu)
    mapper, event_obs_pool, event_det_pool = map_events(picks_TP, set(picks_obs.event_index), set(picks_det.event_index))
    tp = len(mapper)
    fp = len(event_det_pool)
    fn = len(event_obs_pool)

    precision=tp/(tp+fp)
    recall=tp/(tp+fn)
    f1=2*precision*recall/(precision+recall)
    print(F1_template.substitute(type='events', 
                                 precision=precision, recall=recall, 
                                 f1=f1, tp=tp, fp=fp, fn=fn))

    tp, tp_p, tp_s = [0], [0], [0]
    def count_tp(row):
        if row.event_index in mapper and mapper[row.event_index]==row.evid_obs:
            tp[0] += 1
            if row.type == 'P':
                tp_p[0] += 1
            elif row.type == 'S':
                tp_s[0] += 1

    picks_TP.apply(count_tp,axis=1)
    tp, tp_p, tp_s = tp[0], tp_p[0], tp_s[0]
    fn = len(picks_obs) - tp
    fn_p = len(picks_obs[picks_obs['type']=='P']) - tp_p
    fn_s = len(picks_obs[picks_obs['type']=='S']) - tp_s
    fp = len(picks_det) - tp
    fp_p = len(picks_det[picks_det['type']=='P']) - tp_p
    fp_s = len(picks_det[picks_det['type']=='S']) - tp_s
    precision=tp/(tp+fp)
    precision_p = tp_p/(tp_p+fp_p)
    precision_s = tp_s/(tp_s+fp_s)
    recall=tp/(tp+fn)
    recall_p=tp_p/(tp_p+fn_p)
    recall_s=tp_s/(tp_s+fn_s)
    f1=2*precision*recall/(precision+recall)
    f1_p=2*precision_p*recall_p/(precision_p+recall_p)
    f1_s=2*precision_s*recall_s/(precision_s+recall_s)
    print(F1_template.substitute(type='picks', 
                                precision=precision, recall=recall, 
                                f1=f1, tp=tp, fp=fp, fn=fn))
    print(F1_template.substitute(type='P', 
                                 precision=precision_p, recall=recall_p, 
                                 f1=f1_p, tp=tp_p, fp=fp_p, fn=fn_p))
    print(F1_template.substitute(type='S', 
                                 precision=precision_s, recall=recall_s, 
                                 f1=f1_s, tp=tp_s, fp=fp_s, fn=fn_s))
    return mapper

if __name__ == '__main__':
    # pntf = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_tonga/picks_tomodd.csv')
    # pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    # pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))

    # manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    # manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events_2month.csv')
    # manual = manual[manual['event_index'].isin(manual_event.event_index)]
    # manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    # manual = manual[manual['station'].isin(pntf['station'])]

    # # the start and end time is determined by the time range of the predicted picks

    # CalFscore(pntf, manual, UTCDateTime('2019-01-01'), UTCDateTime('2019-02-28T23:59:59'), 20)

    # manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    # manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
    # manual = manual[manual['event_index'].isin(manual_event.event_index)]
    # manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    # start, end = manual['timestamp'].min(), manual['timestamp'].max()
    # isc = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_arrival_reviewed.csv')
    # isc_cat = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_catalog_reviewed.csv')
    # isc_cat = isc_cat[(isc_cat['time'] >= start) & (isc_cat['time'] <= end)]
    # isc = isc[isc['event_index'].isin(isc['event_index'])]
    # isc['timestamp'] = isc['timestamp'].apply(lambda x: UTCDateTime(x))
    # manual = manual[manual['station'].isin(isc['station'])]
    # # pntf = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/picks_tomodd.csv')
    # # pntf_cat = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2/catalogs_tomodd.csv')
    # # pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    # # pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    # # manual = manual[manual['station'].isin(pntf['station'])]
    # # pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))
    # # the start and end time is determined by the time range of the manual picks
    # CalFscore(isc, manual, manual['timestamp'].min(), manual['timestamp'].max(), 20)

    # manual = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/picks_tomodd.csv')
    # manual_event = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/catalogs_tomodd.csv')
    # pntf = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/result/phase_arrivals.csv')
    # pntf = pntf.rename(columns={'time':'timestamp', 'sta':'station', 'phase':'type'})
    # manual = manual[manual['station'].isin(pntf['station'])]
    # manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    # pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))
    # # the start and end time is determined by the time range of the manual picks
    # picks_TP, picks_FN, picks_FP = PickFscore(manual, pntf, manual['timestamp'].min(), manual['timestamp'].max())
    # CalFscore(picks_TP, pntf, manual)

    manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
    pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/picks_gamma.csv')
    pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/catalogs_gamma.csv')
    pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    manual = manual[manual['station'].isin(set(pntf['station']))]
    manual['timestamp'] = manual['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    start, end = manual['timestamp'].min(), manual['timestamp'].max()
    
    # pntf_cat['time'] = pntf_cat['time'].swifter.apply(lambda x: UTCDateTime(x))
    # pntf_cat = pntf_cat[(pntf_cat['time'] >= start) & (pntf_cat['time'] <= end)]
    # pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    # pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    # CalFscore(pntf, manual, manual['timestamp'].min(), manual['timestamp'].max(), 20)
    
    # pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/picks_bootstrap.csv')
    # pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/catalogs_bootstrap.csv')
    # pntf['station'] = pntf['id'].swifter.apply(lambda x: x.split('.')[1])
    # pntf_cat['time'] = pntf_cat['time'].swifter.apply(lambda x: UTCDateTime(x))
    # pntf_cat = pntf_cat[(pntf_cat['time'] >= start) & (pntf_cat['time'] <= end)]
    # pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    # pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    # CalFscore(pntf, manual, manual['timestamp'].min(), manual['timestamp'].max(), 20)

    pntf = pd.read_csv('/mnt/home/jieyaqi/phase_picks-3.csv')
    pntf_cat = pd.read_csv('/mnt/home/jieyaqi/PNTFIter1_catalogs.csv')
    pntf_cat['time'] = pntf_cat['time'].swifter.apply(lambda x: UTCDateTime(x))
    pntf_cat = pntf_cat[(pntf_cat['time'] >= start) & (pntf_cat['time'] <= end)]
    pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    CalFscore(pntf, manual, manual['timestamp'].min(), manual['timestamp'].max(), 20)
    