import os
import numpy as np
from obspy import UTCDateTime
import json
import h5py
import pandas as pd
import sys
sys.path.insert(0, '/mnt/home/jieyaqi/code/AlaskaEQ/general')
from plot import PlotTime

t2str = lambda x: x.__unicode__()
str2t = lambda x: UTCDateTime(x)

def _CalFscore(det: list, obs: list, start: UTCDateTime, end: UTCDateTime, threshold: float):
    det.sort()
    obs.sort()
    TP = []
    FN = []
    FP = []

    if len(det) == 0: 
        if len(obs) == 0:
            pass
        else:
            i = 0
            while i < len(obs):
                if obs[i] >= start and obs[i] <= end:
                    FN.append(t2str(obs[i]))
                i = i + 1
    else:
        if len(obs) == 0:
            FP = [t2str(i) for i in det]
        else:
            i = j = 0
            TP = []
            FN = []
            FP = []
            
            while i < len(obs) and j < len(det) and obs[i] <= end:
                if obs[i] < start:
                    i = i + 1
                    continue
                elif abs(det[j]-obs[i]) <= threshold:
                    TP.append(t2str(det[j]))
                    i = i + 1
                    j = j + 1
                elif obs[i] < det[j] - threshold:
                    FN.append(t2str(obs[i]))
                    i = i + 1
                elif obs[i] > det[j] + threshold:
                    FP.append(t2str(det[j]))
                    j = j + 1

            while j < len(det):
                FP.append(t2str(det[j]))
                j = j + 1

            while i < len(obs) and obs[i] <= end:
                FN.append(t2str(obs[i]))
                i = i + 1
    return TP, FN, FP



class Sta:
    def __init__(self, sta: str, net: str) -> None:
        self.station = sta
        self.network = net
        self.id = f'{self.network}.{self.station}..BH'

    

    def GetData(self, 
                start: UTCDateTime, 
                end: UTCDateTime, 
                minf: float, 
                maxf: float) -> dict:

        st = self.client.get_waveforms(
                self.network, self.station, "*", "*", start, end)
        
        if len(st) == 0:
            return None

        data = {}
        for tr in st:
            tr.filter(type='bandpass', freqmin = minf, freqmax = maxf)
            data[tr.stats.channel] = tr
            
        return data



    def GetPicks(self, 
                 start: UTCDateTime, 
                 end: UTCDateTime,
                 manPicks: pd.DataFrame,
                 prePicks: pd.DataFrame):

        manPicks = manPicks[manPicks['id'] == self.id]
        if len(manPicks) != 0 and isinstance(manPicks['timestamp'].to_numpy()[0], str):
            manPicks['timestamp'] = manPicks['timestamp'].apply(lambda x: UTCDateTime(x))
        manPicks = manPicks[manPicks['timestamp'] >= start]
        manPicks = manPicks[manPicks['timestamp'] <= end]

        prePicks = prePicks[prePicks['id'] == self.id]
        if len(prePicks) != 0 and isinstance(prePicks['timestamp'].to_numpy()[0], str):
            prePicks['timestamp'] = prePicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        prePicks = prePicks[prePicks['timestamp'] >= start]
        prePicks = prePicks[prePicks['timestamp'] <= end]
        
        picks = {'pp': prePicks[prePicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ps': prePicks[prePicks["type"]=="S"]['timestamp'].to_numpy(),
                 'mp': manPicks[manPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ms': manPicks[manPicks["type"]=="S"]['timestamp'].to_numpy()}
        return picks



    def GetProb(self,
                pickt: UTCDateTime):
        
        probf = os.path.join(self.workdir, 
                             'detections', 
                             self.station + '_outputs', 
                             "prediction_probabilities.hdf5")
        try:
            prob = h5py.File(probf, 'r')
        except (FileNotFoundError, OSError):
            prob = None

        if prob != None:
            probslot = list(prob.keys())

            amp = {}
            for ts in probslot:
                t = str2t(ts)

                if pickt >= t and pickt < t + 60:
                    pt = int((pickt - t) * 100)
                    amp[ts] = max(np.array(prob[ts]['P_arrival'])[pt - 2: pt + 2])
                elif t >= pickt + 60:
                    break
            
            ts = max(amp, key = amp.get)
            
            prob_org = {'p': np.array(prob[ts]['P_arrival']),
                        's': np.array(prob[ts]['S_arrival']),
                        'eq': np.array(prob[ts]['Earthquake'])}
                    
        return UTCDateTime(ts), prob_org
            
        

    def CalFscoreSta(self, 
                   start: UTCDateTime, 
                   end: UTCDateTime,
                   manPicks: pd.DataFrame,
                   prePicks: pd.DataFrame, 
                   threshold: float) -> None:
        picks = self.GetPicks(start, end, manPicks, prePicks)

        pTP, pFN, pFP = _CalFscore(picks['pp'], picks['mp'], start, end, threshold)
        sTP, sFN, sFP = _CalFscore(picks['ps'], picks['ms'], start, end, threshold)

        fscore = {'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}, 'manual': {'p': len(picks['mp']), 's': len(picks['ms'])}, 'predict': {'p': len(picks['pp']), 's': len(picks['ps'])}}
        return fscore



    def PlotPick(self, 
                 pickt: UTCDateTime, 
                 minf: float, 
                 maxf: float,
                 manPicks: pd.DataFrame,
                 prePicks: pd.DataFrame) -> None:

        figdir = os.path.join(self.workdir, 'figures', self.station)
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        startt, prob = self.GetProb(pickt)
        if prob == None:
            return
        data = self.GetData(start = startt, 
                                   end = startt + 60, 
                                   minf = minf, 
                                   maxf = maxf)   
        if data == None:
            return      
        picks = self.GetPicks(startt, startt + 60, manPicks, prePicks)

        delta = list(data.values())[0].stats.delta
        pickspt = {}
        for k, v in picks.items():
            pickspt[k] = (v - startt)/delta
            pickspt[k] = [int(x) for x in pickspt[k]]
        
        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, 
                                f'{self.station}:{startt.__unicode__()}')
        PlotTime(fig_name, data, pickspt, delta, prob, 'EQT', 60)



    @classmethod
    def GenJSON(cls) -> dir:
        stationList = {}
        stationCls = {}
        
        net, sta, lat, lon, ele = np.loadtxt(os.path.join(cls.workdir, 'station.txt'), delimiter='|', unpack=True, usecols=(0,1,2,3,4), dtype=str)

        for i in range(len(sta)):

            stationCls[sta[i]] = cls(sta[i], net[i])
            stationList[sta[i]] = {}
            stationList[sta[i]]['network'] = net[i]

            location = [float(lat[i]), float(lon[i]), float(ele[i])]
            stationList[sta[i]]['coords'] = location

            datadir = os.path.join(cls.datadir, sta[i])

            if os.path.isdir(datadir):
                channels = []

                for mseed in os.listdir(datadir):
                    cha, _, _ = mseed.split('.')[3].split('__')
                    channels.append(cha)

                stationList[sta[i]]['channels'] = list(set(channels))

            else:
                del stationCls[sta[i]]
                del stationList[sta[i]]

        with open(os.path.join(cls.workdir, 'station_list.json'), 'w') as f:
            json.dump(stationList, f)

        return stationCls

    
    @classmethod
    def GenSta(cls) -> dir:
        with open(os.path.join(cls.workdir, 'station_list.json'), 'r') as f:
            stationList = json.load(f)

        stationCls = {}
        for sta, item in stationList.items():
            stationCls[sta] = cls(sta, item['network'])

        return stationCls
