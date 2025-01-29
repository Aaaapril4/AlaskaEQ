import pandas as pd
from obspy import UTCDateTime
import multiprocessing as mp
import swifter
from string import Template

F1_template = Template("F1 for $type\n \
    precision: $precision\n \
    recall: $recall\n \
    f1: $f1\n \
    tp: $tp\n \
    fp: $fp\n \
    fn: $fn")

def _CalFscore(det: pd.DataFrame, obs: pd.DataFrame, threshold: float):
    det = det.sort_values('timestamp', ignore_index = True)
    obs = obs.sort_values('timestamp', ignore_index = True)
    TP = pd.DataFrame()
    FN = pd.DataFrame()
    FP = pd.DataFrame()

    if len(det) == 0: 
        if len(obs) == 0:
            pass
        else:
            FN = obs

    else:
        if len(obs) == 0:
            FP = det
        else:
            i = j = 0
            
            while i < len(obs) and j < len(det):
                if abs(det.iloc[j]['timestamp']-obs.iloc[i]['timestamp']) <= threshold:
                    tempdict = dict(det.iloc[j])
                    if 'event_index' in obs.columns:
                        tempdict['evid_obs'] = obs.iloc[i]['event_index']
                    TP = pd.concat([TP, pd.Series(tempdict).to_frame().T])
                    i = i + 1
                    j = j + 1
                elif obs.iloc[i]['timestamp'] < det.iloc[j]['timestamp'] - threshold:
                    FN = pd.concat([FN, obs.iloc[i].to_frame().T])
                    i = i + 1
                elif obs.iloc[i]['timestamp'] > det.iloc[j]['timestamp'] + threshold:
                    FP = pd.concat([FP, det.iloc[j].to_frame().T])
                    j = j + 1

            while j < len(det):
                FP = pd.concat([FP, det.iloc[j].to_frame().T])
                j = j + 1

            while i < len(obs):
                FN = pd.concat([FN, obs.iloc[i].to_frame().T])
                i = i + 1
    return TP, FN, FP



def CalFscore_sta(sta: str, phase_det: pd.DataFrame, phase_obs: pd.DataFrame):
    print(sta)
    obs = phase_obs[phase_obs['station'] == sta]
    det = phase_det[phase_det['station'] == sta]
    obs_p = obs[obs["type"] == "P"]
    obs_s = obs[obs["type"] == "S"]
    det_p = det[det["type"] == "P"]
    det_s = det[det["type"] == "S"]
    pTP, pFN, pFP = _CalFscore(det_p, obs_p, 3)
    sTP, sFN, sFP = _CalFscore(det_s, obs_s, 3)
    TP = pd.concat([pTP, sTP])
    FN = pd.concat([pFN, sFN])
    FP = pd.concat([pFP, sFP])
    return TP, FN, FP



def CalFscore(phase_det: pd.DataFrame, phase_obs: pd.DataFrame, start: UTCDateTime, end: UTCDateTime, ncpu: int = 1):
    phase_obs = phase_obs[(phase_obs['timestamp'] >= start) & (phase_obs['timestamp'] <= end)]
    phase_det = phase_det[(phase_det['timestamp'] >= start) & (phase_det['timestamp'] <= end)]

    TP_all = pd.DataFrame()
    FN_all = pd.DataFrame()
    FP_all = pd.DataFrame()
    with mp.Pool(ncpu) as p:
        result = p.starmap(
            CalFscore_sta,
            [[sta, phase_det, phase_obs] for sta in set(phase_obs['station'])]
        )
    for TP, FN, FP in result:
        TP_all = pd.concat([TP_all, TP])
        FN_all = pd.concat([FN_all, FN])
        FP_all = pd.concat([FP_all, FP])
    
    tp_p, tp_s, fn_p, fn_s, fp_p, fp_s = 0, 0, 0, 0, 0, 0
    if len(TP_all) != 0:
        tp_p = len(TP_all[TP_all['type'] == 'P'])
        tp_s = len(TP_all[TP_all['type'] == 'S'])
    if len(FN_all) != 0:
        fn_p = len(FN_all[FN_all['type'] == 'P'])
        fn_s = len(FN_all[FN_all['type'] == 'S'])
    if len(FP_all) != 0:
        fp_p = len(FP_all[FP_all['type'] == 'P'])
        fp_s = len(FP_all[FP_all['type'] == 'S'])
    precision_p = tp_p/(tp_p+fp_p)
    precision_s = tp_s/(tp_s+fp_s)
    recall_p=tp_p/(tp_p+fn_p)
    recall_s=tp_s/(tp_s+fn_s)
    f1_p=2*precision_p*recall_p/(precision_p+recall_p)
    f1_s=2*precision_s*recall_s/(precision_s+recall_s)
    print(F1_template.substitute(type='prediction_P', 
                            precision=precision_p, recall=recall_p, 
                            f1=f1_p, tp=tp_p, fp=fp_p, fn=fn_p))
    print(F1_template.substitute(type='prediction_S', 
                            precision=precision_s, recall=recall_s, 
                            f1=f1_s, tp=tp_s, fp=fp_s, fn=fn_s))

    return TP_all, FN_all, FP_all



if __name__ == '__main__':
    manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    pntf = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/iter2/picks.csv')
    pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    pntf['timestamp'] = pntf['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    manual = manual[manual['station'].isin(set(pntf['station']))]
    manual['timestamp'] = manual['timestamp'].swifter.apply(lambda x: UTCDateTime(x))
    CalFscore(pntf, manual, manual['timestamp'].min(), manual['timestamp'].max())