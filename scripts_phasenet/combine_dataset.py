import h5py
import pandas as pd
from obspy import UTCDateTime
import numpy as np
from dataclasses import dataclass
import os

@dataclass
class ProcessResult:
    success: bool
    result: tuple


def _CalFscore(det: pd.DataFrame, obs: pd.DataFrame, start: UTCDateTime, end: UTCDateTime, threshold: float):
    det = det.sort_values('phase_time', ignore_index = True)
    obs = obs.sort_values('phase_time', ignore_index = True)
    TP = pd.DataFrame()
    FN = pd.DataFrame()
    FP = pd.DataFrame()

    if len(det) == 0: 
        if len(obs) == 0:
            pass
        else:
            i = 0
            while i < len(obs):
                if obs.iloc[i]['phase_time'] >= start and obs.iloc[i]['phase_time'] < end:
                    FN = pd.concat([FN, obs.iloc[i].to_frame().T])
                i = i + 1
    else:
        if len(obs) == 0:
            FP = det
        else:
            i = j = 0
            
            while i < len(obs) and j < len(det) and obs.iloc[i]['phase_time'] < end:
                if obs.iloc[i]['phase_time'] < start:
                    i = i + 1
                    continue
                elif abs(det.iloc[j]['phase_time']-obs.iloc[i]['phase_time']) <= threshold:
                    tempdict = dict(obs.iloc[i])
                    tempdict['pntf'] = det.iloc[j]['event_id']
                    TP = pd.concat([TP, pd.Series(tempdict).to_frame().T])
                    i = i + 1
                    j = j + 1
                elif obs.iloc[i]['phase_time'] < det.iloc[j]['phase_time'] - threshold:
                    FN = pd.concat([FN, obs.iloc[i].to_frame().T])
                    i = i + 1
                elif obs.iloc[i]['phase_time'] > det.iloc[j]['phase_time'] + threshold:
                    FP = pd.concat([FP, det.iloc[j].to_frame().T])
                    j = j + 1

            while j < len(det):
                FP = pd.concat([FP, det.iloc[j].to_frame().T])
                j = j + 1

            while i < len(obs) and obs.iloc[i]['phase_time'] < end:
                FN = pd.concat([FN, obs.iloc[i].to_frame().T])
                i = i + 1
    return TP, FN, FP


def CalFscore(phase1: pd.DataFrame, phase2: pd.DataFrame):
    # Get true positive and false negtive from dataset
    TP_all = pd.DataFrame()
    FN_all = pd.DataFrame()
    FP_all = pd.DataFrame()
    for sta in set(phase1['station_id']):
        print(sta)
        obs = phase1[phase1['station_id'] == sta]
        det = phase2[phase2['station_id'] == sta]
        obs_p = obs[obs["phase_type"] == "P"]
        obs_s = obs[obs["phase_type"] == "S"]
        det_p = det[det["phase_type"] == "P"]
        det_s = det[det["phase_type"] == "S"]
        pTP, pFN, pFP = _CalFscore(det_p, obs_p, UTCDateTime(2018,1,1), UTCDateTime(2020, 1, 1), 3)
        sTP, sFN, sFP = _CalFscore(det_s, obs_s, UTCDateTime(2018,1,1), UTCDateTime(2020, 1, 1), 3)
        TP = pd.concat([pTP, sTP])
        FN = pd.concat([pFN, sFN])
        FP = pd.concat([pFP, sFP])
        TP_all = pd.concat([TP_all, TP])
        FN_all = pd.concat([FN_all, FN])
        FP_all = pd.concat([FP_all, FP])
    return TP_all, FN_all, FP_all


def Combine_existed_event(pair: str, TP: pd.DataFrame, FN: pd.DataFrame, f: h5py.File, phase3: pd.DataFrame):
    [evid, staid] = pair.split('_')
    processed_iter2 = TP[TP["pair"] == pair]
    notprocessed_iter2 = FN[FN["pair"] == pair]

    if len(processed_iter2) != 1:
        print(f'{pair} has two TPs but comes here')
        return ProcessResult(False, ())
    
    if "S" not in notprocessed_iter2['phase_type'].to_list():
        print(f'{pair} only has FN P')
        return ProcessResult(False, ())
    
    pntf_index = processed_iter2.iloc[0]["pntf"]
    stadata = f[f"/{str(int(pntf_index))}/{staid}"]

    if "S" in stadata.attrs['phase_type']:
        print(f'{pair} has both P and S in iter2')
        return ProcessResult(False, ())
    
    if len(notprocessed_iter2) != 1:
        print(f'{pair} has two FNs but comes here')
        notprocessed_iter2 = notprocessed_iter2[notprocessed_iter2['phase_type'] == 'S'][0:1]
        
    
    pntf_index = processed_iter2.iloc[0]["pntf"]
    stadata = f[f"/{str(int(pntf_index))}/{staid}"]
    
    new_index = np.append(stadata.attrs['phase_index'], 
                int((notprocessed_iter2.iloc[0]['phase_time'] - UTCDateTime(stadata.attrs['begin_time'])) / stadata.attrs['dt_s'])).astype(int)
    new_type = np.append(stadata.attrs['phase_type'], notprocessed_iter2.iloc[0]['phase_type'])
    new_time = np.append(UTCDateTime(stadata.attrs['phase_time'][0]), notprocessed_iter2.iloc[0]['phase_time'])

    if new_index[1] <= new_index[0]:
        print(f'{pair} S cannot earilier than P')
        return ProcessResult(False, ())
    if new_time[1] >= UTCDateTime(stadata.attrs['end_time']):
        print(f'{pair} S out of length')
        return ProcessResult(False, ())

    stadata.attrs['phase_type'] = [str(x) for x in new_type]
    stadata.attrs['phase_index'] = new_index
    stadata.attrs['phase_polarity'] = ['', '']
    stadata.attrs['phase_score'] = [1, 1]
    stadata.attrs['phase_time'] = [str(x) for x in new_time]

    a = {
        'event_id': str(int(pntf_index)),
        'station_id': staid,
        'phase_index': new_index[1],
        'phase_time': new_time[1],
        'phase_score': 1,
        'phase_type': new_type[1],
        'phase_polarity': ''
        }
    phase = pd.Series(a).to_frame().T
    phase3 = pd.concat([phase3, phase], ignore_index=True)
    return ProcessResult(True, (phase3, f))



if __name__ == '__main__':
    cat1 = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/catalogs.csv')
    cat2 = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/catalogs_iter2.csv')
    phase1 = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/phase_picks.csv')
    phase2 = pd.read_csv('/mnt/scratch/jieyaqi/alaska/final/phase_picks_iter2.csv')
    phase1['phase_time'] = phase1['phase_time'].apply(lambda x: UTCDateTime(x))
    phase2['phase_time'] = phase2['phase_time'].apply(lambda x: UTCDateTime(x))
    phase1.sort_values("phase_time")
    phase2.sort_values("phase_time")

    TP, FN, FP = CalFscore(phase1, phase2)
    TP['pair'] = TP.apply(lambda x: f'{x["event_id"]}_{x["station_id"]}', axis = 1)
    FN['pair'] = FN.apply(lambda x: f'{x["event_id"]}_{x["station_id"]}', axis = 1)

    # Combine dataset
    f1 = h5py.File('/mnt/scratch/jieyaqi/alaska/final/Alaska.hdf5', 'r')
    f2 = h5py.File('/mnt/scratch/jieyaqi/alaska/final/Alaska_iter2.hdf5', 'r')
    f3name = '/mnt/scratch/jieyaqi/alaska/final/Alaska_combined.hdf5'
    os.system(f'cp /mnt/scratch/jieyaqi/alaska/final/Alaska_iter2.hdf5 {f3name}')
    f3 = h5py.File(f3name, 'a')

    cat3 = pd.DataFrame()
    phase3 = pd.DataFrame()

    
    for pair in set(FN['pair']):
        [evid, staid] = pair.split('_')
        # check if TP exist
        if pair in TP["pair"].to_list():
            processresult = Combine_existed_event(pair, TP, FN, f3, phase3)
            if processresult.success:
                phase3, f3 = processresult.result
            continue
        
        if f"/{evid}" not in f3:
            evdf = cat1[cat1['event_id'] == evid]
            evmeta = {
                'begin_time': '', 
                'depth_km': evdf.iloc[0]['depth_km'], 
                'end_time': '', 
                'event_id': evdf.iloc[0]['event_id'], 
                'event_time': evdf.iloc[0]['event_time'], 
                'event_time_index': -1, 
                'latitude': evdf.iloc[0]['latitude'], 
                'longitude': evdf.iloc[0]['longitude'], 
                'magnitude': evdf.iloc[0]['magnitude'], 
                'magnitude_type': '', 
                'source': 'AEC'
                }

            evdata = f3.create_group(evid)
            for k, v in evmeta.items():
                evdata.attrs[k] = v
            catalog = pd.Series(evmeta).to_frame().T
            cat3 = pd.concat([cat3, catalog], ignore_index=True)

            # add phase data and meta
            f1.copy(f'/{evid}/{staid}', f3, f'/{evid}/{staid}')
            stameta = dict(f3[f'/{evid}/{staid}'].attrs)
            for i in range(len(stameta['phase_index'])):
                a = {
                    'event_id': evid,
                    'station_id': staid,
                    'phase_index': stameta['phase_index'][i],
                    'phase_time': stameta['phase_time'][i],
                    'phase_score': 1,
                    'phase_type': stameta['phase_type'][i],
                    'phase_polarity': ''
                }
                phase = pd.Series(a).to_frame().T
                phase3 = pd.concat([phase3, phase], ignore_index=True)
        else:
            f1.copy(f'/{evid}/{staid}', f3, f'/{evid}/{staid}')
            stameta = dict(f3[f'/{evid}/{staid}'].attrs)
            for i in range(len(stameta['phase_index'])):
                a = {
                    'event_id': evid,
                    'station_id': staid,
                    'phase_index': stameta['phase_index'][i],
                    'phase_time': stameta['phase_time'][i],
                    'phase_score': 1,
                    'phase_type': stameta['phase_type'][i],
                    'phase_polarity': ''
                }
                phase = pd.Series(a).to_frame().T
                phase3 = pd.concat([phase3, phase], ignore_index=True)


    f1.close()
    f2.close()
    f3.close()

    phase3 = pd.concat([phase2, phase3])
    cat3 = pd.concat([cat2, cat3])
    phase3.to_csv('/mnt/scratch/jieyaqi/alaska/final/phase_picks_combined.csv', index=False)
    cat3.to_csv('/mnt/scratch/jieyaqi/alaska/final/catalogs_combined.csv', index=False)