import os
import shutil
import numpy as np
from obspy import UTCDateTime
import obspy
import calendar
import pandas as pd
from plot import PlotTime

t2str = lambda x: x.__unicode__()
str2t = lambda x: UTCDateTime(x)

def _CalFscore(det: list, obs: list, start: UTCDateTime, end: UTCDateTime, threshold: float):
    TP = []
    FN = []
    FP = []
    utc2str = lambda x: x.__unicode__()

    if det == None or len(det) == 0: 
        if obs == None or len(obs) == 0:
            pass
        else:
            i = 0
            while i < len(obs):
                if obs[i] >= start and obs[i] <= end:
                    FN.append(utc2str(obs[i]))
                i = i + 1
    else:
        if len(obs) == 0:
            FP = [utc2str(i) for i in det]
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
                    TP.append(utc2str(det[j]))
                    i = i + 1
                    j = j + 1
                elif obs[i] < det[j] - threshold:
                    FN.append(utc2str(obs[i]))
                    i = i + 1
                elif obs[i] > det[j] + threshold:
                    FP.append(utc2str(det[j]))
                    j = j + 1

            while j < len(det):
                FP.append(utc2str(det[j]))
                j = j + 1

            while i < len(obs) and obs[i] <= start:
                FN.append(utc2str(obs[i]))
                i = i + 1
    return TP, FN, FP



class Sta:
    def __init__(self, 
                 net: str,
                 sta: str, 
                 start: str,
                 end: str) -> None:
        self.station = sta
        self.network = net
        self.start = UTCDateTime(start)
        self.end = UTCDateTime(end)



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

        manSta = manPicks[manPicks['id'] == f'{self.network}.{self.station}..BH']
        manSta = manSta[manSta['timestamp'] >= start]
        manSta = manSta[manSta['timestamp'] <= end]

        preSta = prePicks[prePicks['id'] == f'{self.network}.{self.station}..BH']
        preSta = preSta[preSta['timestamp'] >= start]
        preSta = preSta[preSta['timestamp'] <= end]
        
        picks = {'pp': preSta[preSta["type"]=="P"]['timestamp'].to_numpy(),
                 'ps': preSta[preSta["type"]=="S"]['timestamp'].to_numpy(),
                 'mp': manSta[manSta["type"]=="P"]['timestamp'].to_numpy(),
                 'ms': manSta[manSta["type"]=="S"]['timestamp'].to_numpy()}
        return picks
    


    def PlotPick(self, 
                 start: UTCDateTime, 
                 minf: float, 
                 maxf: float,
                 manPicks: pd.DataFrame,
                 prePicks: pd.DataFrame) -> None:
        figdir = os.path.join(self.workdir, 'figures', self.station)
        if os.path.isdir(figdir):
            shutil.rmtree(figdir)
        os.makedirs(figdir)

        data = self.GetData(start = start, end = start + 120, minf = minf, maxf = maxf)         
        picks = self.GetPicks(start, start + 120, manPicks, prePicks)
        prob = self.GetProb(start, start + 120)

        delta = list(data.values())[0].stats.delta
        pickspt = {}
        for k, v in picks.items():
            pickspt[k] = (v - start)/delta
            pickspt[k] = [int(x) for x in pickspt[k]]
        
        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, f'{self.station}:{start.__unicode__()}')
        PlotTime(fig_name, data, pickspt, delta, prob)