from sta import Sta
import pandas as pd
import os
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client
from itertools import repeat
import multiprocessing as mp
import random



def Process(stacls, manPicks, prePicks, lock = None, value = None):
    fscore = stacls.CalFscoreSta(start = UTCDateTime(2019,1,1),
                        end = UTCDateTime(2019,3,1),
                        manPicks = manPicks,
                        prePicks = prePicks,
                        threshold = 1)

    # for i in range(5):
    #     t = UTCDateTime(random.choice(fscore['p']['TP']))
    #     stacls.PlotPick(start = t - 5,
    #                     minf = 2, 
    #                     maxf = 20,
    #                     manPicks = manPicks,
    #                     prePicks = prePicks)
    #     t = UTCDateTime(random.choice(fscore['p']['FN']))
    #     stacls.PlotPick(start = t - 5,
    #                     minf = 2, 
    #                     maxf = 20,
    #                     manPicks = manPicks,
    #                     prePicks = prePicks)
    #     t = UTCDateTime(random.choice(fscore['p']['FP']))
    #     stacls.PlotPick(start = t - 5,
    #                     minf = 2, 
    #                     maxf = 20,
    #                     manPicks = manPicks,
    #                     prePicks = prePicks)
        
    if lock != None:
        with lock:
            a = dict(value)
            a['p']['TP'] += len(fscore['p']['TP'])
            a['p']['FN'] += len(fscore['p']['FN'])
            a['p']['FP'] += len(fscore['p']['FP'])
            a['s']['TP'] += len(fscore['s']['TP'])
            a['s']['FN'] += len(fscore['s']['FN'])
            a['s']['FP'] += len(fscore['s']['FP'])
            a['all']['TP'] += (len(fscore['p']['TP']) + len(fscore['s']['TP']))
            a['all']['FN'] += (len(fscore['p']['FN']) + len(fscore['s']['FN']))
            a['all']['FP'] += (len(fscore['p']['FP']) + len(fscore['s']['FP']))
            a['manual']['p'] += fscore['manual']['p']
            a['manual']['s'] += fscore['manual']['s']
            a['predict']['p'] += fscore['predict']['p']
            a['predict']['s'] += fscore['predict']['s']

            value.update(a)




if __name__ == '__main__':
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/phasenet'
    Sta.client = Client('/mnt/scratch/jieyaqi/alaska/phasenet/timeseries.sqlite')
    datadir = os.path.join(Sta.workdir, 'data')
    parameter = {'filter':{'p': 0.3, 's': 0.3},
                 'ncpu': 40}
    stationCls = Sta.GenSta(datadir)

    # Prepare figure directory
    if not os.path.isdir(os.path.join(Sta.workdir, 'figures')):
        os.makedirs(os.path.join(Sta.workdir, 'figures'))

    # Process prediction result if not
    if not os.path.isfile(os.path.join(Sta.workdir, 'picks.csv')):
        prePicks = pd.read_csv(os.path.join(Sta.workdir, 'result', 'phase_arrivals.csv'))
        prePicks = prePicks[["net", "sta", "phase", "time", "amp"]]
        prePicksP = prePicks[prePicks["phase"] == "TP"]
        prePicksP = prePicksP[prePicksP['amp'] >= parameter['filter']['p']]
        prePicksP.columns = ["network", "station", "type", "timestamp", "prob"]
        prePicksP['type'] = 'P'

        prePicksS = prePicks[prePicks["phase"] == "TS"]
        prePicksS = prePicksS[prePicksS['amp'] >= parameter['filter']['s']]
        prePicksS.columns = ["network", "station", "type", "timestamp", "prob"]
        prePicksS['type'] = 'S'

        prePicks = pd.concat([prePicksP, prePicksS])
        prePicks['id'] = prePicks.apply(lambda x: f'{x["network"]}.{x["station"]}..BH'.replace(' ', ''), axis = 1)
        prePicks.to_csv(os.path.join(Sta.workdir, 'picks.csv'),
                        index=False, 
                        float_format="%.3f",
                        date_format='%Y-%m-%dT%H:%M:%S.%f')
    else:
        prePicks = pd.read_csv(os.path.join(Sta.workdir, 'picks.csv'))

    manPicks = pd.read_csv('data/manualPicks.csv')

    Process(stationCls['ACH'], manPicks, prePicks)
    
    manager = mp.Manager()
    lock = manager.Lock()
    fscore_all = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
                              's':{'TP': 0, 'FN': 0, 'FP':0},
                              'all': {'TP': 0, 'FN': 0, 'FP': 0},
                              'manual': {'p': 0, 's': 0},
                              'predict': {'p': 0, 's': 0}})
    
    with mp.Pool(parameter['ncpu']) as p:
        p.starmap(Process, zip(stationCls.values(), repeat(manPicks), repeat(prePicks), repeat(lock), repeat(fscore_all)))
    
    print(dict(fscore_all))