import os
import shutil
import numpy as np
from obspy import UTCDateTime
import json
import h5py
import obspy
from plot import PlotTime

t2str = lambda x: x.__unicode__()
str2t = lambda x: UTCDateTime(x)

class Sta:
    def __init__(self, sta: str, net: str) -> None:
        self.name = sta
        self.network = net



    def SetChan(self, cha: list) -> None:
        self.channel = cha



    def SetCoor(self, cor: list) -> None:
        self.latitude = cor[0]
        self.longitude = cor[1]
        self.elevation = cor[2]



    def SetTime(self) -> None:
        bt = UTCDateTime.now()
        et = UTCDateTime(1900,1,1,0,0)
        datadir = os.path.join(self.workdir,'data', self.name)

        for f in os.listdir(datadir):
            tbt = str2t(f.split('.')[3].split('__')[1])
            tet = str2t(f.split('.')[3].split('__')[2])

            if tbt < bt:
                bt = tbt

            if tet > et:
                et = tet

        self.start = bt
        self.end = et

    

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
        pickprob = {'p': {}, 's': {}}
        try:
            parrival, pprob, sarrival, sprob = np.loadtxt(predf, unpack = True, dtype = str, delimiter = ',', usecols = (11, 12, 15, 16), skiprows=1)
        except:
            self.detP = []
            self.detS = []
        else:
            p = []
            s = []

            for i in range(len(parrival)): 
                if parrival[i] != '':
                    t = str2t(parrival[i])
                    tlabel = t.strftime('%Y%m%d')
                    ot = UTCDateTime(year = t.year, month = t.month, day = t.day)
                    if tlabel not in pickprob['p'].keys():
                        pickprob['p'][tlabel] = []
                    pickprob['p'][tlabel].append(f'{t - ot} {pprob[i]} 0.0 \n')
                    p.append(t)
                if sarrival[i] != '':
                    t = str2t(sarrival[i])
                    tlabel = t.strftime('%Y%m%d')
                    ot = UTCDateTime(year = t.year, month = t.month, day = t.day)
                    if tlabel not in pickprob['s'].keys():
                        pickprob['s'][tlabel] = []
                    pickprob['s'][tlabel].append(f'{t - ot} {sprob[i]} 0.0 \n')                    
                    s.append(t)

            for tlabel, data in pickprob['p'].items():
                with open(os.path.join(self.workdir, 'association', tlabel, f'{self.network}.{self.name}.P'), 'w') as f:
                    f.writelines(data)
            for tlabel, data in pickprob['s'].items():
                with open(os.path.join(self.workdir, 'association', tlabel, f'{self.network}.{self.name}.S'), 'w') as f:
                    f.writelines(data)

            self.detP = p
            self.detS = s
            self.detP.sort()
            self.detS.sort()


    
    def CalFscore(self, threshold) -> None:
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

        fscoref = os.path.join(self.workdir, 'detections', self.name+'_outputs', 'Fscore.json')
        if os.path.isfile(fscoref):
            with open(fscoref, 'r') as f:
                self.fscore = json.load(f)

        if (not os.path.isfile(fscoref)) or (self.fscore['threshold'] != threshold):
            pTP, pFN, pFP = _CalFscore(self.detP, self.manP, self.start, self.end, threshold)
            sTP, sFN, sFP = _CalFscore(self.detS, self.manS, self.start, self.end, threshold)

            self.fscore = {'threshold': threshold,'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}}
            with open(fscoref, 'w') as f:
                json.dump(self.fscore, f)
    
    
    
    def PlotEvent(self, start: UTCDateTime, end: UTCDateTime, minf: float, maxf: float) -> None:
        figdir = os.path.join(self.workdir, 'figures', self.name)
        if os.path.isdir(figdir):
            shutil.rmtree(figdir)
        os.makedirs(figdir)

        # Load probability
        probf = os.path.join(self.workdir, 'detections', self.name + '_outputs', "prediction_probabilities.hdf5")
        prob = h5py.File(probf, 'r')
        timeslot = list(prob.keys())

        # Load data file
        data_time = {}
        for f in os.listdir(os.path.join(self.workdir, 'data', self.name)):
            st = f.split('__')[1]
            cha = f.split('__')[0].split('.')[-1]
            if st not in data_time.keys():
                data_time[st] = {}
            if cha not in data_time[st].keys():
                data_time[st][cha] = f
        
        indicator = [0, 0, 0, 0]

        for ts in timeslot:
            t = str2t(ts)

            if t >= start and t <= end:
                dpt = []
                dst = []
                mpt = []
                mst = []
                
                # Get data
                data = {}
                for dt in data_time.keys():
                    if t >= UTCDateTime(dt) and t + 60 <= UTCDateTime(dt) + 60 * 60 * 24 * 30:
                        for c in data_time[dt].keys():
                            tempstream = obspy.read(os.path.join(self.workdir, 'data', self.name, data_time[dt][c]))
                            for tr in tempstream:
                                if t >= tr.stats.starttime and end <= tr.stats.endtime:
                                    tr.detrend('demean')
                                    tr.filter(type='bandpass', freqmin = minf, freqmax = maxf)
                                    tr.taper(max_percentage=0.001, type='cosine', max_length=2) 
                                    delta = tr.stats.delta
                                    be = int((t - tr.stats.starttime) / delta)
                                    ne = int((t - tr.stats.starttime + 60) / delta)
                                    data[c] = tr.data[be:ne+1]
                                    break

                j = indicator[0]
                while self.detP[j] < t + 60:
                    if self.detP[j] >= t:
                        pt = int((self.detP[j] - t) / 0.01)
                        pmax = max(prob[ts]['P_arrival'][pt-2: pt+2])
                        if pmax > self.parameter['p']:
                            dpt.append((self.detP[j] - t)/delta)
                    else:
                        indicator[0] = j
                    j = j + 1

                j = indicator[1]
                while self.detS[j] < t + 60:
                    if self.detS[j] >= t:
                        pt = int((self.detS[j] - t) / 0.01)
                        pmax = max(prob[ts]['S_arrival'][pt-2: pt+2])
                        if pmax > self.parameter['s']:
                            dst.append((self.detS[j] - t)/delta)
                    else:
                        indicator[1] = j
                    j = j + 1

                j = indicator[2]
                while self.manP[j] < t + 60:
                    if self.manP[j] >= t:
                        mpt.append((self.manP[j] - t)/delta)
                    else:
                        indicator[2] = j
                    j = j + 1

                j = indicator[3]
                while self.manS[j] < t + 60:
                    if self.manS[j] >= t:
                        mst.append((self.manS[j] - t)/delta)
                    else:
                        indicator[3] = j
                    j = j + 1
                
                fig_name = os.path.join(figdir, ts)
                PlotTime(fig_name, data, mpt, mst, dpt, dst, delta, prob[ts]['Earthquake'], prob[ts]['P_arrival'], prob[ts]['S_arrival'])
            
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

            datadir = os.path.join(cls.workdir, 'data', sta[i])

            if os.path.isdir(datadir):
                bt = UTCDateTime.now()
                et = UTCDateTime(1900,1,1,0,0)
                channels = []

                for mseed in os.listdir(datadir):
                    cha, tbt, tet = mseed.split('.')[3].split('__')
                    tbt = str2t(tbt)
                    tet = str2t(tet)

                    if tbt < bt:
                        bt = tbt

                    if tet > et:
                        et = tet

                    channels.append(cha)

                stationCls[sta[i]].start = bt
                stationCls[sta[i]].end = et
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
