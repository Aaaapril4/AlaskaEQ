from sta import Sta
import pandas as pd
import os
from event import Event
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client
from itertools import repeat
import multiprocessing as mp
import random



def Process(stacls, lock = None, fscoreall_pre = None, fscoreall_aso = None):
    fscore_pre, fscore_aso = stacls.CalFscoreSta(start = UTCDateTime(2019,1,1),
                        end = UTCDateTime(2019,3,1),
                        threshold = 1)

    # for i in range(5):
    #     if len(fscore_aso['p']['TP']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['TP']))
    #         stacls.PlotPick(start = t - 10,
    #                         minf = 0.5, 
    #                         maxf = 10)
    #     if len(fscore_aso['p']['FN']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['FN']))
    #         stacls.PlotPick(start = t - 10,
    #                         minf = 0.5, 
    #                         maxf = 10)
    #     if len(fscore_aso['p']['FP']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['FP']))
    #         stacls.PlotPick(start = t - 10,
    #                         minf = 0.5, 
    #                         maxf = 10)
        
    if lock != None:
        with lock:
            a = dict(fscoreall_pre)
            a['p']['TP'] += len(fscore_pre['p']['TP'])
            a['p']['FN'] += len(fscore_pre['p']['FN'])
            a['p']['FP'] += len(fscore_pre['p']['FP'])
            a['s']['TP'] += len(fscore_pre['s']['TP'])
            a['s']['FN'] += len(fscore_pre['s']['FN'])
            a['s']['FP'] += len(fscore_pre['s']['FP'])
            a['all']['TP'] += (len(fscore_pre['p']['TP']) + len(fscore_pre['s']['TP']))
            a['all']['FN'] += (len(fscore_pre['p']['FN']) + len(fscore_pre['s']['FN']))
            a['all']['FP'] += (len(fscore_pre['p']['FP']) + len(fscore_pre['s']['FP']))
            a['manual']['p'] += fscore_pre['manual']['p']
            a['manual']['s'] += fscore_pre['manual']['s']
            a['predict']['p'] += fscore_pre['predict']['p']
            a['predict']['s'] += fscore_pre['predict']['s']
            fscoreall_pre.update(a)

            a = dict(fscoreall_aso)
            a['p']['TP'] += len(fscore_aso['p']['TP'])
            a['p']['FN'] += len(fscore_aso['p']['FN'])
            a['p']['FP'] += len(fscore_aso['p']['FP'])
            a['s']['TP'] += len(fscore_aso['s']['TP'])
            a['s']['FN'] += len(fscore_aso['s']['FN'])
            a['s']['FP'] += len(fscore_aso['s']['FP'])
            a['all']['TP'] += (len(fscore_aso['p']['TP']) + len(fscore_aso['s']['TP']))
            a['all']['FN'] += (len(fscore_aso['p']['FN']) + len(fscore_aso['s']['FN']))
            a['all']['FP'] += (len(fscore_aso['p']['FP']) + len(fscore_aso['s']['FP']))
            a['manual']['p'] += fscore_aso['manual']['p']
            a['manual']['s'] += fscore_aso['manual']['s']
            a['predict']['p'] += fscore_aso['predict']['p']
            a['predict']['s'] += fscore_aso['predict']['s']
            fscoreall_aso.update(a)



if __name__ == '__main__':
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/phasenet_wins'
    Event.workdir = Sta.workdir
    Sta.client = Client('/mnt/scratch/jieyaqi/alaska/timeseries.sqlite') # with instrumental response
    Sta.client = Client('/mnt/scratch/jieyaqi/alaska/phasenet/timeseries.sqlite')
    datadir = os.path.join(Sta.workdir, 'data')
    parameter = {'filter':{'p': 0.5, 's': 0.5},
                 'ncpu': 20}
    stationCls = Sta.GenSta(datadir)

    # Prepare figure directory
    if not os.path.isdir(os.path.join(Sta.workdir, 'figures')):
        os.makedirs(os.path.join(Sta.workdir, 'figures'))

    # Process prediction result if not
    if not os.path.isfile(os.path.join(Sta.workdir, 'picks.csv')):
        prePicks = pd.read_csv(os.path.join(Sta.workdir, 'result', 'phase_arrivals.csv'))
        prePicks = prePicks[["net", "sta", "phase", "time", "amp"]]
        prePicksP = prePicks[prePicks["phase"] == "P"]
        prePicksP = prePicksP[prePicksP['amp'] >= parameter['filter']['p']]
        prePicksP.columns = ["network", "station", "type", "timestamp", "prob"]
        prePicksP['type'] = 'P'

        prePicksS = prePicks[prePicks["phase"] == "S"]
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
    asoPicks = pd.read_csv(os.path.join(Sta.workdir, 'picks_gamma.csv'))
    
    Sta.manPicks = manPicks
    Sta.prePicks = prePicks
    Sta.asoPicks = asoPicks

    # t = UTCDateTime('2019-01-28T07:48:00.959000Z') + 10
    # stationCls['LT07'].PlotPick(start = t - 10,
    #                         minf = 0.5, 
    #                         maxf = 10)
    # Process(stationCls['ACH'])
    ################################## Calculate F-score ##################################
    manager = mp.Manager()
    lock = manager.Lock()
    fscore_pre = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
                              's':{'TP': 0, 'FN': 0, 'FP':0},
                              'all': {'TP': 0, 'FN': 0, 'FP': 0},
                              'manual': {'p': 0, 's': 0},
                              'predict': {'p': 0, 's': 0}})
    
    fscore_aso = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
                              's':{'TP': 0, 'FN': 0, 'FP':0},
                              'all': {'TP': 0, 'FN': 0, 'FP': 0},
                              'manual': {'p': 0, 's': 0},
                              'predict': {'p': 0, 's': 0}})
    
    with mp.Pool(parameter['ncpu']) as p:
        p.starmap(Process, zip(stationCls.values(), repeat(lock), repeat(fscore_pre), repeat(fscore_aso)))
    
    precision_p = fscore_pre['p']['TP']/(fscore_pre['p']['TP']+fscore_pre['p']['FP'])
    precision_s = fscore_pre['s']['TP']/(fscore_pre['s']['TP']+fscore_pre['s']['FP'])
    precision_all = fscore_pre['all']['TP']/(fscore_pre['all']['TP']+fscore_pre['all']['FP'])
    recall_p = fscore_pre['p']['TP']/(fscore_pre['p']['TP']+fscore_pre['p']['FN'])
    recall_s = fscore_pre['s']['TP']/(fscore_pre['s']['TP']+fscore_pre['s']['FN'])
    recall_all = fscore_pre['all']['TP']/(fscore_pre['all']['TP']+fscore_pre['all']['FN'])
    print(dict(fscore_pre))
    print(f'precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')

    precision_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FP'])
    precision_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FP'])
    precision_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FP'])
    recall_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FN'])
    recall_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FN'])
    recall_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FN'])
    print(dict(fscore_aso))
    print(f'ASSOCIATION precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')
	
    ################################## Plot waveforms for events ##################################
    ev = Event(57.193,-160.193,401, UTCDateTime('2019-01-03T20:51:22.562000Z'), 811)
    ev.Plot(stationCls, 0.5, 10, 1, 0, 4, True)