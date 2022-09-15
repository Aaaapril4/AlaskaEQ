import os
import numpy as np
from obspy import UTCDateTime
import json

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
            tbt = UTCDateTime(f.split('.')[3].split('__')[1])
            tet = UTCDateTime(f.split('.')[3].split('__')[2])

            if tbt < bt:
                bt = tbt

            if tet > et:
                et = tet

        self.start = bt
        self.end = et

    
    def SetManualPick(self, manPicks: dir) -> None:
        if self.name in manPicks:
            self.manP = manPicks[self.name]['P']
            self.manS = manPicks[self.name]['S']
        else:
            self.manP = []
            self.manS = []


    def SortPred(self) -> None:
        predf = os.path.join(self.workdir, 'detections', self.name+'_outputs', "X_prediction_results.csv")

        try:
            parrival, sarrival = np.loadtxt(predf, unpack = True, dtype = str, delimiter = ',', usecols = (11, 15), skiprows=1)
        except:
            self.detP = []
            self.detS = []
        else:
            p = []
            s = []

            for i in range(len(parrival)):
                if parrival[i] != '':
                    p.append(UTCDateTime('T'.join(parrival[i].split(' '))))
                if sarrival[i] != '':
                    s.append(UTCDateTime('T'.join(sarrival[i].split(' '))))

            self.detP = p
            self.detS = s


    def CalFscore(self) -> None:
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
                    obs.sort()
                    det.sort()
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
    
        pTP, pFN, pFP = _CalFscore(self.detP, self.manP, self.start, self.end, 1)
        sTP, sFN, sFP = _CalFscore(self.detS, self.manS, self.start, self.end, 1)

        with open(os.path.join(self.workdir, 'detections', self.name+'_outputs', 'Fscore.json'), 'w') as f:
            json.dump({'p': {'TP': pTP, 'FN': pFN, 'FP': pFP}, 's': {'TP': sTP, 'FN': sFN, 'FP': sFP}}, f)
        

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
                    tbt = UTCDateTime(tbt)
                    tet = UTCDateTime(tet)

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
