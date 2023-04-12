import os
from obspy import UTCDateTime
import obspy
import pandas as pd
import sys
import numpy as np
sys.path.insert(1, '/mnt/home/jieyaqi/code/AlaskaEQ/general')
from plot import PlotTime
from pathlib import Path

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
    def __init__(self, 
                 sta: str,
                 net: str) -> None:
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

        data = {}
        for tr in st:
            tr.filter(type='bandpass', freqmin = minf, freqmax = maxf)
            data[tr.stats.channel] = tr
            
        return data


    
    def GetProb(self,
                 start: UTCDateTime,
                 end: UTCDateTime) -> dict:
        
        fname = f'{self.network}.{self.station}.' \
                + start.strftime('%Y-%m-%dT%H:00:00.000000Z') \
                + '.' \
                + (start + 60 * 60).strftime('%Y-%m-%dT%H:00:00.000000Z') \
                + '.prediction.mseed'
        f = os.path.join(self.workdir, 'result', fname)
        st = obspy.read(f)
        start_sample = int((start - UTCDateTime(fname.split('.')[2])) / st[0].stats.delta)
        end_sample = int((end - UTCDateTime(fname.split('.')[2])) / st[0].stats.delta)
        data = {'p': st[0].data[start_sample : end_sample + 1],
                's': st[1].data[start_sample : end_sample + 1],
                'ps': st[2].data[start_sample : end_sample + 1]}

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
    


    def PlotPick(self, 
                 start: UTCDateTime, 
                 minf: float, 
                 maxf: float,
                 manPicks: pd.DataFrame,
                 prePicks: pd.DataFrame) -> None:
        
        figdir = os.path.join(self.workdir, 'figures', self.station)
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        data = self.GetData(start = start, end = start + 60, minf = minf, maxf = maxf)         
        picks = self.GetPicks(start, start + 60, manPicks, prePicks)
        prob = self.GetProb(start, start + 60)

        delta = list(data.values())[0].stats.delta
        pickspt = {}
        for k, v in picks.items():
            pickspt[k] = (v - start)/delta
            pickspt[k] = [int(x) for x in pickspt[k]]
        
        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, f'{self.station}:{start.__unicode__()}')
        PlotTime(fig_name, data, pickspt, delta, prob, 'PN-TF', 60)



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



    @classmethod
    def GenSta(cls, datadir) -> dir:
        stationCls = {}
        
        data = Path(datadir)
        net, sta, _, _, _ = np.loadtxt(os.path.join(cls.workdir, 'station.txt'), delimiter='|', unpack=True, usecols=(0,1,2,3,4), dtype=str)

        for i in range(len(sta)):
            stationCls[sta[i]] = cls(sta[i], net[i]) 

            if len(sorted(data.glob(f'{net[i]}.{sta[i]}*'))) == 0:
                del stationCls[sta[i]]        

        return stationCls



    @classmethod
    def CalFscore(self, 
                    start: UTCDateTime, 
                    end: UTCDateTime,
                    manPicks: pd.DataFrame,
                    prePicks: pd.DataFrame, 
                    threshold: float) -> None:
        
        manPicks = manPicks[manPicks['timestamp'] >= start]
        manPicks = manPicks[manPicks['timestamp'] <= end]
        prePicks = prePicks[prePicks['timestamp'] >= start]
        prePicks = prePicks[prePicks['timestamp'] <= end]
        
        preP = prePicks[prePicks["type"]=="P"]['timestamp'].to_numpy()
        preS = prePicks[prePicks["type"]=="S"]['timestamp'].to_numpy()
        manP = manPicks[manPicks["type"]=="P"]['timestamp'].to_numpy()
        manS = manPicks[manPicks["type"]=="S"]['timestamp'].to_numpy()
        
        pTP, pFN, pFP = _CalFscore(preP, manP, start, end, threshold)
        sTP, sFN, sFP = _CalFscore(preS, manS, start, end, threshold)

        precision_p = len(pTP) / (len(pTP) + len(pFP))
        precision_s = len(sTP) / (len(sTP) + len(sFP))
        precision = (len(pTP)+len(sTP))/(len(pTP)+len(sTP)+len(pFP)+len(sFP))
        recall_p = len(pTP) / (len(pTP) + len(pFN))
        recall_s = len(sTP) / (len(sTP) + len(sFN))
        recall = (len(sTP)+len(pTP))/(len(sTP)+len(pTP)+len(pFN)+len(sFN))

        fscore = {'threshold': threshold, 'Fscore': {'precision': precision, 'recall': recall}, 'p': {'precision': precision_p, 'recall': recall_p}, 's': {'precision': precision_s, 'recall': recall_s}}
        return fscore