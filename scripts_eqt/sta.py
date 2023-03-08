import os
import shutil
import numpy as np
from obspy import UTCDateTime
import json
import h5py
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
    def __init__(self, sta: str, net: str) -> None:
        self.name = sta
        self.network = net



    def SetChan(self, cha: list) -> None:
        self.channel = cha


    
    def SetID(self) -> None:
        try:
            self.id = f'{self.network}.{self.name}..{self.channel[0][:-1]}'
        except:
            self.id = ''



    def SetCoor(self, cor: list) -> None:
        self.latitude = cor[0]
        self.longitude = cor[1]
        self.elevation = cor[2]



    def SetTime(self) -> None:
        bt = UTCDateTime.now()
        et = UTCDateTime(1900,1,1,0,0)
        datadir = os.path.join(self.datadir, self.name)

        data_time = {}

        for f in os.listdir(datadir):
            cha, tbt, tet = f.split('.')[3].split('__')

            if tbt not in data_time.keys():
                data_time[tbt] = {}
            if cha not in data_time[tbt].keys():
                data_time[tbt][cha] = f

            if tbt < bt:
                bt = tbt

            if tet > et:
                et = tet

        self.start = bt
        self.end = et
        self.data_time = data_time

    

    def LoadManualPick(self, manPicks: dir) -> None:
        if self.name in manPicks:
            self.manP = manPicks[self.name]['P']
            self.manS = manPicks[self.name]['S']
            self.manP.sort()
            self.manS.sort()
        else:
            self.manP = []
            self.manS = []



    def LoadPred(self) -> None:
        predf = os.path.join(self.workdir, 'detections', self.name+'_outputs', "X_prediction_results.csv")
        try:
            parrival, pprob, sarrival, sprob = np.loadtxt(predf, unpack = True, dtype = str, delimiter = ',', usecols = (11, 12, 15, 16), skiprows=1)
        except:
            self.detP = []
            self.detS = []
        else:
            p = []
            s = []
            prob4asso = []
            t4asso = []
            type4asso = []

            for i in range(len(parrival)): 
                if parrival[i] != '':
                    t = str2t(parrival[i])
                    prob4asso.append(pprob[i])
                    t4asso.append(parrival[i])
                    type4asso.append('P')
                    p.append(t)
                if sarrival[i] != '':
                    t = str2t(sarrival[i])  
                    prob4asso.append(sprob[i])
                    t4asso.append(sarrival[i])
                    type4asso.append('S')            
                    s.append(t)

            np.savetxt(os.path.join(self.workdir, 'detections', self.name+'_outputs', "picks.csv"), np.column_stack(([self.id]*len(t4asso), t4asso, type4asso, prob4asso, [0]*len(t4asso))), fmt='%s', delimiter=',')

            self.detP = p
            self.detS = s
            self.detP.sort()
            self.detS.sort()


    
    def LoadProb(self) -> None:
        probf = os.path.join(self.workdir, 'detections', self.name + '_outputs', "prediction_probabilities.hdf5")
        try:
            self.prob = h5py.File(probf, 'r')
        except (FileNotFoundError, OSError):
            self.prob = None
            
        

    def CalFscore(self, threshold) -> None:
        if self.prob != None:
            fscoref = os.path.join(self.workdir, 'detections', self.name+'_outputs', 'Fscore.json')
            if os.path.isfile(fscoref):
                with open(fscoref, 'r') as f:
                    self.fscore = json.load(f)

            if (not os.path.isfile(fscoref)) or (not ('threshold' in self.fscore.keys())) or (self.fscore['threshold'] != threshold):
                pTP, pFN, pFP = _CalFscore(self.detP, self.manP, self.start, self.end, threshold)
                sTP, sFN, sFP = _CalFscore(self.detS, self.manS, self.start, self.end, threshold)
                try:
                    precision = (len(pTP)+len(sTP))/(len(pTP)+len(sTP)+len(pFP)+len(sFP))
                    recall = (len(sTP)+len(pTP))/(len(sTP)+len(pTP)+len(pFN)+len(sFN))
                except ZeroDivisionError:
                    precision = None
                    recall = None
                self.fscore = {'threshold': threshold, 'Fscore': {'precision': precision, 'recall': recall}, 'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}}
                with open(fscoref, 'w') as f:
                    json.dump(self.fscore, f)
    
    

    def GetData(self, start: UTCDateTime, end: UTCDateTime, minf: float, maxf: float):
        data = {}
        delta = 0
        for dt in self.data_time.keys():
            dtt = UTCDateTime(dt)
            if start >= dtt and end <= dtt + 60 * 60 * 24 * calendar.monthrange(dtt.year, dtt.month)[1]:
                for c in self.data_time[dt].keys():
                    tempstream = obspy.read(os.path.join(self.datadir, self.name, self.data_time[dt][c]))
                    for tr in tempstream:
                        if start >= tr.stats.starttime and end <= tr.stats.endtime:
                            tr.detrend('demean')
                            tr.filter(type='bandpass', freqmin = minf, freqmax = maxf)
                            # tr.filter(type='highpass', freq = minf)
                            delta = tr.stats.delta
                            be = int((start - tr.stats.starttime) / delta)
                            ne = int((end - tr.stats.starttime) / delta)
                            data[c] = tr.data[be:ne+1]
                            break
        if delta == 0:
            return None, 0
        else:
            return data, delta
        


    def GetPicks(self, start: UTCDateTime, end: UTCDateTime, delta: float, ts: str = None, outt: bool = False):
        dpt = []
        dst = []
        mpt = []
        mst = []
        
        if hasattr(self, 'detP'):
            j = 0
            while j < len(self.detP) and self.detP[j] < end:
                if self.detP[j] >= start:
                    pt = int((self.detP[j] - start) / 0.01)
                    if ts != None:
                        pmax = max(self.prob[ts]['P_arrival'][pt-5: pt+5])
                        if pmax > self.parameter['p']:
                            dpt.append((self.detP[j] - start)/delta)
                    else:
                        if not outt:
                            dpt.append((self.detP[j] - start)/delta)
                        else:
                            dpt.append()
                j = j + 1
        else:
            dpt = []

        if hasattr(self, 'detS'):
            j = 0
            while j < len(self.detS) and self.detS[j] < end:
                if self.detS[j] >= start:
                    pt = int((self.detS[j] - start) / 0.01)
                    if ts != None:
                        pmax = max(self.prob[ts]['S_arrival'][pt-2: pt+2])
                        if pmax > self.parameter['s']:
                            dst.append((self.detS[j] - start)/delta)
                    else:
                        dst.append((self.detS[j] - start)/delta)
                j = j + 1
        else:
            dst = []

        if hasattr(self, 'manP'):
            j = 0
            while j < len(self.manP) and self.manP[j] < end:
                if self.manP[j] >= start:
                    mpt.append((self.manP[j] - start)/delta)
                j = j + 1
        else:
            mpt = []

        if hasattr(self, 'manS'):
            j = 0
            while j < len(self.manS) and self.manS[j] < end:
                if self.manS[j] >= start:
                    mst.append((self.manS[j] - start)/delta)
                j = j + 1
        else:
            mst = []
            
        return dpt, dst, mpt, mst



    def LoadAPred(self, picks):
        if self.id != '':
            pickssta = picks[picks.id == self.id]
            self.AdetP = list(pickssta[pickssta.type == 'P']['timestamp'])
            self.AdetS = list(pickssta[pickssta.type == 'S']['timestamp'])
        else:
            self.AdetP = []
            self.AdetS = []



    def CalAFscore(self, threshold) -> None:
        fscoref = os.path.join(self.workdir, 'detections', self.name+'_outputs', 'Fscore.json')
        if os.path.isfile(fscoref):
            with open(fscoref, 'r') as f:
                self.fscore = json.load(f)

        if (not os.path.isfile(fscoref)) or (not ('threshold' in self.fscore.keys())) or (self.fscore['threshold'] != threshold):
            pTP, pFN, pFP = _CalFscore(self.AdetP, self.manP, self.start, self.end, threshold)
            sTP, sFN, sFP = _CalFscore(self.AdetS, self.manS, self.start, self.end, threshold)
            try:
                precision = (len(pTP)+len(sTP))/(len(pTP)+len(sTP)+len(pFP)+len(sFP))
                recall = (len(sTP)+len(pTP))/(len(sTP)+len(pTP)+len(pFN)+len(sFN))
            except ZeroDivisionError:
                precision = None
                recall = None
            self.fscore = {'threshold': threshold, 'Fscore': {'precision': precision, 'recall': recall}, 'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}}
            with open(fscoref, 'w') as f:
                json.dump(self.fscore, f)



    def PlotPick(self, start: UTCDateTime, end: UTCDateTime, minf: float, maxf: float) -> None:
        figdir = os.path.join(self.workdir, 'figures', self.name)
        if os.path.isdir(figdir):
            shutil.rmtree(figdir)
        os.makedirs(figdir)

        if self.prob != None:
            probslot = list(self.prob.keys())

            for ts in probslot:
                t = str2t(ts)

                if t >= start and t <= end:
    
                    data, delta = self.GetData(start = t, end = t + 60, minf = minf, maxf = maxf)         
                    dpt, dst, mpt, mst = self.GetPicks(t, t + 60, delta, ts)
                    
                    fig_name = os.path.join(figdir, f'{self.name}:{t.__unicode__()}')
                    PlotTime(fig_name, data, mpt, mst, dpt, dst, delta, self.prob[ts]['Earthquake'], self.prob[ts]['P_arrival'], self.prob[ts]['S_arrival'])
                
                elif t > end:
                    break



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
            stationCls[sta[i]].SetCoor(location)

            datadir = os.path.join(cls.datadir, sta[i])

            if os.path.isdir(datadir):
                bt = UTCDateTime.now()
                et = UTCDateTime(1900,1,1,0,0)
                channels = []

                data_time = {}
                for mseed in os.listdir(datadir):
                    cha, tb, te = mseed.split('.')[3].split('__')
                    tbt = str2t(tb)
                    tet = str2t(te)

                    if tb not in data_time.keys():
                        data_time[tb] = {}
                    if cha not in data_time[tb].keys():
                        data_time[tb][cha] = mseed

                    if tbt < bt:
                        bt = tbt

                    if tet > et:
                        et = tet

                    channels.append(cha)

                stationCls[sta[i]].start = bt
                stationCls[sta[i]].end = et
                stationCls[sta[i]].data_time = data_time
                stationCls[sta[i]].SetChan = list(set(channels))
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
            stationCls[sta].SetChan(item['channels'])
            stationCls[sta].SetCoor(item['coords'])
            stationCls[sta].SetTime()

        return stationCls
