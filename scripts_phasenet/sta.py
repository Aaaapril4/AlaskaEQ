import os
from obspy import UTCDateTime
import obspy
import pandas as pd
import sys
import numpy as np
sys.path.insert(1, '/mnt/home/jieyaqi/code/AlaskaEQ/general')
from plot import PlotTimePNTF
from pathlib import Path
from nnAudio import features
import torch

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



def Calfft(data, sampling_rate, freqmin, freqmax, n_fft=256, max_clamp=3000):
    spec_layer=features.STFT(
            n_fft=n_fft,
            hop_length=1,
            output_format="Magnitude",
            window="hann",
            verbose=False
        )
    
    df = (sampling_rate / 2) / (n_fft // 2)
    freqmin_pos = round(freqmin / df)
    freqmax_pos = round(freqmax / df)
    sgrams = {}
    vmax = {}
    for key, value in data.items():
        sgram = spec_layer(torch.from_numpy(value.data).to(torch.float32))
        sgram = sgram[..., freqmin_pos : freqmax_pos + 1, :-1]
        sgrams[key] = sgram.numpy()
        vmax[key] = (sgram[..., round(2 / df) : round(8 / df) + 1, :-1]).max().numpy()

    return sgrams, vmax



class Sta:
    def __init__(self, 
                 sta: str,
                 net: str,
                 lat: float,
                 lon: float) -> None:
        self.station = sta
        self.network = net
        self.longitude = lon
        self.latitude = lat
        self.id = f'{self.network}.{self.station}..BH'



    def GetData(self, 
                start: UTCDateTime, 
                end: UTCDateTime, 
                minf: float, 
                maxf: float) -> dict:

        st = self.client.get_waveforms(
                self.network, self.station, "*", "*", start - 60, end + 60)

        if len(st) == 0:
            return None
        
        data = {}
        for tr in st:
            tr.filter(type='bandpass', freqmin = minf, freqmax = maxf)
            if tr.stats.delta != 0.025:
                tr.interpolate(sampling_rate=40)
            tr.trim(start, end)
            tr.normalize()
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
                's': st[1].data[start_sample : end_sample + 1]}

        return data
    


    def GetPicks(self, 
                 start: UTCDateTime, 
                 end: UTCDateTime,
                 index: int = None):

        manPicks = self.manPicks[self.manPicks['id'] == self.id]
        if len(manPicks) != 0 and isinstance(manPicks['timestamp'].to_numpy()[0], str):
            manPicks['timestamp'] = manPicks['timestamp'].apply(lambda x: UTCDateTime(x))
        manPicks = manPicks[manPicks['timestamp'] >= start]
        manPicks = manPicks[manPicks['timestamp'] <= end]

        prePicks = self.prePicks[self.prePicks['id'] == self.id]
        if len(prePicks) != 0 and isinstance(prePicks['timestamp'].to_numpy()[0], str):
            prePicks['timestamp'] = prePicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        prePicks = prePicks[prePicks['timestamp'] >= start]
        prePicks = prePicks[prePicks['timestamp'] <= end]
        
        asoPicks = self.asoPicks[self.asoPicks['id'] == self.id]
        if index == None:
            asoPicks = asoPicks[asoPicks['event_index'] != -1]
        else:
            asoPicks = asoPicks[asoPicks['event_index'] == index]
        if len(asoPicks) != 0 and isinstance(asoPicks['timestamp'].to_numpy()[0], str):
            asoPicks['timestamp'] = asoPicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        asoPicks = asoPicks[asoPicks['timestamp'] >= start]
        asoPicks = asoPicks[asoPicks['timestamp'] <= end]

        picks = {'pp': prePicks[prePicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ps': prePicks[prePicks["type"]=="S"]['timestamp'].to_numpy(),
                 'mp': manPicks[manPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ms': manPicks[manPicks["type"]=="S"]['timestamp'].to_numpy(),
                 'ap': asoPicks[asoPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'as': asoPicks[asoPicks["type"]=="S"]['timestamp'].to_numpy()}
        return picks
    


    def PlotPick(self, 
                 start: UTCDateTime, 
                 minf: float, 
                 maxf: float) -> None:
        
        figdir = os.path.join(self.workdir, 'figures', self.station)
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        data = self.GetData(start = start, end = start + 60, minf = minf, maxf = maxf)
        sgrams, vmax = Calfft(data, 40, minf, maxf) 
        picks = self.GetPicks(start, start + 60)
        prob = self.GetProb(start, start + 60)

        delta = list(data.values())[0].stats.delta
        pickspt = {}
        for k, v in picks.items():
            pickspt[k] = (v - start)/delta
            pickspt[k] = [int(x) for x in pickspt[k]]

        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, f'{self.network}.{self.station}:{start.__unicode__()}')
        PlotTimePNTF(fig_name, data, sgrams, vmax, pickspt, delta, prob, 'PN-TF', [minf, maxf], 60)



    def CalFscoreSta(self, 
                   start: UTCDateTime, 
                   end: UTCDateTime,
                   threshold: float) -> None:
        picks = self.GetPicks(start, end)

        pTP, pFN, pFP = _CalFscore(picks['pp'], picks['mp'], start, end, threshold)
        sTP, sFN, sFP = _CalFscore(picks['ps'], picks['ms'], start, end, threshold)

        fscore_pre = {'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}, 'manual': {'p': len(picks['mp']), 's': len(picks['ms'])}, 'predict': {'p': len(picks['pp']), 's': len(picks['ps'])}}

        pTP, pFN, pFP = _CalFscore(picks['ap'], picks['mp'], start, end, threshold)
        sTP, sFN, sFP = _CalFscore(picks['as'], picks['ms'], start, end, threshold)

        fscore_aso = {'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}, 'manual': {'p': len(picks['mp']), 's': len(picks['ms'])}, 'predict': {'p': len(picks['ap']), 's': len(picks['as'])}}
        return fscore_pre, fscore_aso



    @classmethod
    def GenSta(cls, datadir) -> dir:
        stationCls = {}
        
        data = Path(datadir)
        net, sta, lat, lon = np.loadtxt(os.path.join(cls.workdir, 'station.txt'), delimiter='|', unpack=True, usecols=(0,1,2,3), dtype=str)

        for i in range(len(sta)):
            stationCls[sta[i]] = cls(sta[i], net[i], lat[i], lon[i]) 

            if len(sorted(data.glob(f'{net[i]}.{sta[i]}*'))) == 0:
                del stationCls[sta[i]]        

        return stationCls