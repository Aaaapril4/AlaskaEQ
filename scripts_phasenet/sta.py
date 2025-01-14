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
                if obs[i] >= start and obs[i] < end:
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
            
            while i < len(obs) and j < len(det) and obs[i] < end:
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

            while i < len(obs) and obs[i] < end:
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
        self.longitude = float(lon)
        self.latitude = float(lat)
        self.id = f'{self.network}.{self.station}..BH'



    def Process(self, st):
        if len(st) == 0:
            return
        st.detrend("linear")
        st.detrend("demean")
        st.taper(max_percentage=0.002, type="hann")

        try:
            st.interpolate(sampling_rate=40)
        except ValueError:
            for tr in st:
                try:
                    tr.interpolate(sampling_rate=40)
                except ValueError:
                    st.remove(tr)
        st.merge(method=1, fill_value="latest")

        if len(st) == 0:
            return
        
        # mask to 0
        masks = []
        st.sort()
        for i in range(len(st)):
            if type(st[i].data) == np.ma.MaskedArray:
                masks.append(st[i].data.mask)
            else:
                masks.append(np.zeros(len(st[i].data), dtype=bool))

        for i in range(len(st)):
            st[i].data[masks[i]] = 0

        if len(st) == 0:
            return
        
        # padding other channels if none
        channels = []
        for tr in st:
            channels.append(tr.stats.channel[2])

        if 'Z' not in channels:
            trz = st[0].copy()
            trz.data = np.zeros(len(trz.data))
            trz.stats.channel = st[0].stats.channel[:2]+'Z'
            st.append(trz)

        if 'E' not in channels and '1' not in channels:
            tre = st[0].copy()
            tre.data = np.zeros(len(tre.data))
            tre.stats.channel = st[0].stats.channel[:2]+'E'
            st.append(tre)

        if 'N' not in channels and '2' not in channels:
            trn = st[0].copy()
            trn.data = np.zeros(len(trn.data))
            trn.stats.channel = st[0].stats.channel[:2]+'N'
            st.append(trn)

        st.sort()
        return st



    def GetData(self, 
                start: UTCDateTime, 
                end: UTCDateTime, 
                minf: float, 
                maxf: float) -> dict:

        st = self.client.get_waveforms(
                "*", self.station, "*", "*", start - 60, end + 60)
        st = self.Process(st)

        if st == None or len(st) == 0:
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
        try:
            st = obspy.read(f)
        except:
            return None
        start_sample = int((start - UTCDateTime(fname.split('.')[2])) / st[0].stats.delta)
        end_sample = int((end - UTCDateTime(fname.split('.')[2])) / st[0].stats.delta)
        data = {'p': st[0].data[start_sample : end_sample + 1],
                's': st[1].data[start_sample : end_sample + 1]}

        return data
    


    def GetPicks(self, 
                 start: UTCDateTime, 
                 end: UTCDateTime,
                 index: int = None):

        manPicks = self.manPicks[self.manPicks['station'] == self.station]
        if len(manPicks) != 0 and isinstance(manPicks['timestamp'].to_numpy()[0], str):
            manPicks['timestamp'] = manPicks['timestamp'].apply(lambda x: UTCDateTime(x))
        manPicks = manPicks[manPicks['timestamp'] >= start]
        manPicks = manPicks[manPicks['timestamp'] < end]

        prePicks = self.prePicks[self.prePicks['station'] == self.station]
        if len(prePicks) != 0 and isinstance(prePicks['timestamp'].to_numpy()[0], str):
            prePicks['timestamp'] = prePicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        prePicks = prePicks[prePicks['timestamp'] >= start]
        prePicks = prePicks[prePicks['timestamp'] < end]
        
        asoPicks = self.asoPicks[self.asoPicks['station'] == self.station]
        if index == None:
            asoPicks = asoPicks[asoPicks['event_index'] != -1]
        else:
            asoPicks = asoPicks[asoPicks['event_index'] == index]
        if len(asoPicks) != 0 and isinstance(asoPicks['timestamp'].to_numpy()[0], str):
            asoPicks['timestamp'] = asoPicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        asoPicks = asoPicks[asoPicks['timestamp'] >= start]
        asoPicks = asoPicks[asoPicks['timestamp'] < end]

        reloPicks = self.reloPicks[self.reloPicks['station'] == self.station]
        if index == None:
            reloPicks = reloPicks[reloPicks['event_index'] != -1]
        else:
            reloPicks = reloPicks[reloPicks['event_index'] == index]
        if len(reloPicks) != 0 and isinstance(reloPicks['timestamp'].to_numpy()[0], str):
            reloPicks['timestamp'] = reloPicks['timestamp'].apply(lambda x: UTCDateTime('T'.join(x.split(' '))))
        reloPicks = reloPicks[reloPicks['timestamp'] >= start]
        reloPicks = reloPicks[reloPicks['timestamp'] < end]

        picks = {'pp': prePicks[prePicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ps': prePicks[prePicks["type"]=="S"]['timestamp'].to_numpy(),
                 'mp': manPicks[manPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'ms': manPicks[manPicks["type"]=="S"]['timestamp'].to_numpy(),
                 'ap': asoPicks[asoPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'as': asoPicks[asoPicks["type"]=="S"]['timestamp'].to_numpy(),
                 'rp': reloPicks[reloPicks["type"]=="P"]['timestamp'].to_numpy(),
                 'rs': reloPicks[reloPicks["type"]=="S"]['timestamp'].to_numpy()}
        return picks
    


    def PlotPick(self, 
                 start: UTCDateTime, 
                 minf: float, 
                 maxf: float,
                 event_index: float = -1) -> None:
        
        figdir = os.path.join(self.workdir, 'figures', self.station)
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        data = self.GetData(start = start, end = start + 60, minf = minf, maxf = maxf)
        if data == None:
            return
        sgrams, vmax = Calfft(data, 40, minf, maxf) 
        picks = self.GetPicks(start, start + 60)
        prob = self.GetProb(start, start + 60)
        if prob == None:
            return
        delta = list(data.values())[0].stats.delta
        pickspt = {}
        for k, v in picks.items():
            pickspt[k] = (v - start)/delta
            pickspt[k] = [int(x) for x in pickspt[k]]

        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, f'{event_index}  {self.network}.{self.station}:{start.__unicode__()}')
        PlotTimePNTF(fig_name, data, sgrams, vmax, pickspt, delta, prob, 'PN-TF', [minf, maxf], 60)

    

    def Plot(self, 
            figdir: str,
            start: UTCDateTime, 
            end: UTCDateTime,
            minf: float, 
            maxf: float,
            remove_instrument: bool = False) -> None:
        
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        data = self.GetData(start = start, end = end, minf = minf, maxf = maxf)
        if data == None:
            return
        sgrams, vmax = Calfft(data, 40, minf, maxf) 

        delta = list(data.values())[0].stats.delta

        for k, v in data.items():
            data[k] = v.data
        
        fig_name = os.path.join(figdir, f'{self.network}.{self.station}:{start.__unicode__()}')
        PlotTimePNTF(fig_name, data, sgrams, vmax, None, delta, None, 'PN-TF', [minf, maxf], end - start)



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

        pTP, pFN, pFP = _CalFscore(picks['rp'], picks['mp'], start, end, threshold)
        sTP, sFN, sFP = _CalFscore(picks['rs'], picks['ms'], start, end, threshold)

        fscore_relo = {'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}, 'manual': {'p': len(picks['mp']), 's': len(picks['ms'])}, 'predict': {'p': len(picks['rp']), 's': len(picks['rs'])}}
        return fscore_pre, fscore_aso, fscore_relo



    @classmethod
    def GenSta(cls, datadir) -> dir:
        stationCls = {}
        
        net, sta, lat, lon = np.loadtxt('/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', delimiter='|', unpack=True, usecols=(0,1,2,3), dtype=str, skiprows=1)

        for i in range(len(sta)):
            stationCls[sta[i]] = cls(sta[i], net[i], lat[i], lon[i]) 

        return stationCls