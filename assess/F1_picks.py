import pandas as pd
from obspy import UTCDateTime


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


def CalFscore(phase_obs: pd.DataFrame, phase_det: pd.DataFrame, start: UTCDateTime, end: UTCDateTime):
    phase_obs = phase_obs[(phase_obs['timestamp'] >= start) & (phase_obs['timestamp'] <= end)]
    phase_det = phase_det[(phase_det['timestamp'] >= start) & (phase_det['timestamp'] <= end)]

    TP_all = pd.DataFrame()
    FN_all = pd.DataFrame()
    FP_all = pd.DataFrame()
    for sta in set(phase_obs['station']):
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
        TP_all = pd.concat([TP_all, TP])
        FN_all = pd.concat([FN_all, FN])
        FP_all = pd.concat([FP_all, FP])
    return TP_all, FN_all, FP_all


if __name__ == '__main__':
    manual = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    manual['timestamp'] = manual['timestamp'].apply(lambda x: UTCDateTime(x))
    pntf = pd.read_csv('/mnt/scratch/jieyaqi/alaska/manual_pick_test/picks_tomodd_Alaska.csv')
    pntf['station'] = pntf['id'].apply(lambda x: x.split('.')[1])
    pntf['timestamp'] = pntf['timestamp'].apply(lambda x: UTCDateTime(x))

    CalFscore(manual, pntf, manual['timestamp'].min(), manual['timestamp'].max())