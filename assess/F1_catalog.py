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
               event_obs_pool:set, 
               event_det_pool:set,
               event_obs: pd.DataFrame,
               event_det: pd.DataFrame):
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
    
    # check if origintime diff
    for evid_det, evid_obs in list(mapper.items()):
        
        ori_det = UTCDateTime(event_det[event_det['event_index'] == evid_det].iloc[0]['time'])
        ori_obs = UTCDateTime(event_obs[event_obs['event_index'] == evid_obs].iloc[0]['time'])

        if ori_det - ori_obs > 15:
            event_obs_pool.add(evid_obs)
            event_det_pool.add(evid_det)
            del mapper[evid_det]

    return mapper, event_obs_pool, event_det_pool


def CalFscore(picks_det: pd.DataFrame, picks_obs: pd.DataFrame, event_det: pd.DataFrame, event_obs: pd.DataFrame, start: UTCDateTime, end: UTCDateTime, ncpu: int = 1):
    
    picks_TP, picks_FN, picks_FP = PickFscore(picks_det, picks_obs, start, end, ncpu)
    mapper, event_obs_pool, event_det_pool = map_events(picks_TP, set(picks_obs.event_index), set(picks_det.event_index), event_obs, event_det)
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
    # # Assessment of model comparison
    # pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/model_comparison/eqt_2month/picks_tomodd.csv')
    # pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/model_comparison/eqt_2month/catalogs_tomodd.csv')
    # pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    # pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))

    # manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    # manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events_2month.csv')
    # manual = manual[manual['event_index'].isin(manual_event.event_index)]
    # manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    # manual = manual[manual['station'].isin(pntf['station'])]

    # CalFscore(pntf, manual, pntf_cat, manual_event, UTCDateTime('2019-01-01'), UTCDateTime('2019-02-28T23:59:59'), 20)


    # # Assessment of associator
    # pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/manual_pick_test/picks_tomodd_constant.csv')
    # pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/manual_pick_test/catalogs_tomodd_constant.csv')
    # pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    # pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))

    # manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    # manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
    # manual = manual[manual['event_index'].isin(manual_event.event_index)]
    # manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    # manual = manual[manual['station'].isin(pntf['station'])]

    # CalFscore(pntf, manual, pntf_cat, manual_event, manual['timestamp'].min(), manual['timestamp'].max(), 20)


    manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
    pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/picks_gamma.csv')
    pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/catalogs_gamma.csv')
    pntf['station'] = pntf['id'].swifter.apply(lambda x: x.split('.')[1])
    manual = manual[manual['station'].isin(set(pntf['station']))]
    manual['timestamp'] = manual['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    start, end = manual['timestamp'].min(), manual['timestamp'].max()
    
    pntf_cat['time'] = pntf_cat['time'].swifter.apply(lambda x: UTCDateTime(x))
    pntf_cat = pntf_cat[(pntf_cat['time'] >= start) & (pntf_cat['time'] <= end)]
    pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    CalFscore(pntf, manual, pntf_cat, manual_event, manual['timestamp'].min(), manual['timestamp'].max(), 20)
    

    manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    manual_event = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/events.csv')
    pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/picks_bootstrap.csv')
    pntf_cat = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/catalogs_bootstrap.csv')
    pntf['station'] = pntf['id'].swifter.apply(lambda x: x.split('.')[1])
    manual = manual[manual['station'].isin(set(pntf['station']))]
    manual['timestamp'] = manual['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    start, end = manual['timestamp'].min(), manual['timestamp'].max()
    
    pntf_cat['time'] = pntf_cat['time'].swifter.apply(lambda x: UTCDateTime(x))
    pntf_cat = pntf_cat[(pntf_cat['time'] >= start) & (pntf_cat['time'] <= end)]
    pntf = pntf[pntf['event_index'].isin(pntf_cat['event_index'])]
    pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    CalFscore(pntf, manual, pntf_cat, manual_event, manual['timestamp'].min(), manual['timestamp'].max(), 20)
    