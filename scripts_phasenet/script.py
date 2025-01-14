from sta import Sta
import pandas as pd
import os
from event import Event
from obspy import UTCDateTime
from obspy.clients.filesystem.tsindex import Client
from itertools import repeat
import multiprocessing as mp
import random



def Process(stacls, lock = None, fscoreall_pre = None, fscoreall_aso = None, fscoreall_relo = None):
    fscore_pre, fscore_aso, fscore_relo = stacls.CalFscoreSta(start = UTCDateTime(2019,1, 1),
                        end = UTCDateTime(2019,3,1),
                        threshold = 1)

    for i in range(2):
        if len(fscore_relo['p']['TP']) != 0:
            t = UTCDateTime(random.choice(fscore_pre['p']['TP']))
            stacls.PlotPick(start = t - 10,
                            minf = 0.5, 
                            maxf = 10)
        # if len(fscore_relo['p']['FN']) != 0:
        #     t = UTCDateTime(random.choice(fscore_pre['p']['FN']))
        #     stacls.PlotPick(start = t - 10,
        #                     minf = 0.5, 
        #                     maxf = 10)
    #     if len(fscore_relo['p']['FP']) != 0:
    #         t = UTCDateTime(random.choice(fscore_pre['p']['FP']))
    #         stacls.PlotPick(start = t - 10,
    #                         minf = 0.5, 
    #                         maxf = 10)
    # print(stacls.station, stacls.network, len(fscore_pre['p']['FN']), len(fscore_pre['s']['FN'])) 
    # if lock != None:
    #     with lock:
    #         a = dict(fscoreall_pre)
    #         a['p']['TP'] += len(fscore_pre['p']['TP'])
    #         a['p']['FN'] += len(fscore_pre['p']['FN'])
    #         a['p']['FP'] += len(fscore_pre['p']['FP'])
    #         a['s']['TP'] += len(fscore_pre['s']['TP'])
    #         a['s']['FN'] += len(fscore_pre['s']['FN'])
    #         a['s']['FP'] += len(fscore_pre['s']['FP'])
    #         a['all']['TP'] += (len(fscore_pre['p']['TP']) + len(fscore_pre['s']['TP']))
    #         a['all']['FN'] += (len(fscore_pre['p']['FN']) + len(fscore_pre['s']['FN']))
    #         a['all']['FP'] += (len(fscore_pre['p']['FP']) + len(fscore_pre['s']['FP']))
    #         a['manual']['p'] += fscore_pre['manual']['p']
    #         a['manual']['s'] += fscore_pre['manual']['s']
    #         a['predict']['p'] += fscore_pre['predict']['p']
    #         a['predict']['s'] += fscore_pre['predict']['s']
    #         fscoreall_pre.update(a)

    #         a = dict(fscoreall_aso)
    #         a['p']['TP'] += len(fscore_aso['p']['TP'])
    #         a['p']['FN'] += len(fscore_aso['p']['FN'])
    #         a['p']['FP'] += len(fscore_aso['p']['FP'])
    #         a['s']['TP'] += len(fscore_aso['s']['TP'])
    #         a['s']['FN'] += len(fscore_aso['s']['FN'])
    #         a['s']['FP'] += len(fscore_aso['s']['FP'])
    #         a['all']['TP'] += (len(fscore_aso['p']['TP']) + len(fscore_aso['s']['TP']))
    #         a['all']['FN'] += (len(fscore_aso['p']['FN']) + len(fscore_aso['s']['FN']))
    #         a['all']['FP'] += (len(fscore_aso['p']['FP']) + len(fscore_aso['s']['FP']))
    #         a['manual']['p'] += fscore_aso['manual']['p']
    #         a['manual']['s'] += fscore_aso['manual']['s']
    #         a['predict']['p'] += fscore_aso['predict']['p']
    #         a['predict']['s'] += fscore_aso['predict']['s']
    #         fscoreall_aso.update(a)

    #         a = dict(fscoreall_relo)
    #         a['p']['TP'] += len(fscore_relo['p']['TP'])
    #         a['p']['FN'] += len(fscore_relo['p']['FN'])
    #         a['p']['FP'] += len(fscore_relo['p']['FP'])
    #         a['s']['TP'] += len(fscore_relo['s']['TP'])
    #         a['s']['FN'] += len(fscore_relo['s']['FN'])
    #         a['s']['FP'] += len(fscore_relo['s']['FP'])
    #         a['all']['TP'] += (len(fscore_relo['p']['TP']) + len(fscore_relo['s']['TP']))
    #         a['all']['FN'] += (len(fscore_relo['p']['FN']) + len(fscore_relo['s']['FN']))
    #         a['all']['FP'] += (len(fscore_relo['p']['FP']) + len(fscore_relo['s']['FP']))
    #         a['manual']['p'] += fscore_relo['manual']['p']
    #         a['manual']['s'] += fscore_relo['manual']['s']
    #         a['predict']['p'] += fscore_relo['predict']['p']
    #         a['predict']['s'] += fscore_relo['predict']['s']
    #         fscoreall_relo.update(a)



if __name__ == '__main__':
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_noIns'
    Event.workdir = Sta.workdir
    # Sta.client = Client(os.path.join(Sta.workdir, 'timeseries.sqlite'))
    # Sta.client = Client('/mnt/scratch/jieyaqi/alaska/alaska_data.sqlite')
    datadir = os.path.join(Sta.workdir, 'data')
    parameter = {'filter':{'p': 0.5, 's': 0.5},
                 'ncpu': 1}
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
        prePicks = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/model_comparison/pntf_alaska/picks_raw.csv')
    
    prePicks['station'] = prePicks['sta']
    prePicks['timestamp'] = prePicks['time']
    prePicks['type'] = prePicks['phase']
    manPicks = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/manual_picks_filltered2.csv')
    manPicks['station'] = manPicks['id'].apply(lambda x: x.split('.')[1])
    asoPicks = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/model_comparison/pntf_alaska/picks_gamma.csv')
    asoPicks['station'] = asoPicks['id'].apply(lambda x: x.split('.')[1])
    reloPicks = pd.read_csv('/mnt/ufs18/nodr/home/jieyaqi/alaska/AlaskaEQ/model_comparison/pntf_alaska/picks_tomodd.csv')
    reloPicks['station'] = reloPicks['id'].apply(lambda x: x.split('.')[1])

    Sta.manPicks = manPicks
    Sta.prePicks = prePicks
    # Sta.asoPicks = None
    # Sta.reloPicks = None
    Sta.asoPicks = asoPicks
    Sta.reloPicks = reloPicks
    Sta.client = Client('/mnt/scratch/jieyaqi/alaska/data.sqlite')
    
    def plot_eventpicks(event_index):
        ks13 = reloPicks[reloPicks["id"] == 'XO.KS13..BH']
        ld41 = reloPicks[reloPicks["id"] == 'XO.LD41..BH']
        ks13_event = ks13[ks13['event_index'] == event_index]['timestamp'].iloc[0]
        ld41_event = ld41[ld41['event_index'] == event_index]['timestamp'].iloc[0]
        stationCls['KS13'].PlotPick(start = UTCDateTime(ks13_event) - 10, minf = 2, maxf = 10, event_index = event_index)
        stationCls['LD41'].PlotPick(start = UTCDateTime(ld41_event) - 10, minf = 2, maxf = 10, event_index = event_index)
    
    plot_eventpicks(482)
    # ks13 = reloPicks[reloPicks["id"] == 'XO.KS13..BH']
    # ld41 = reloPicks[reloPicks["id"] == 'XO.LD41..BH']
    # ks13_482 = ks13[ks13['event_index'] == 482]['timestamp'].iloc[0]
    # ld41_482 = ld41[ld41['event_index'] == 482]['timestamp'].iloc[0]
    # stationCls['KS13'].PlotPick(start = UTCDateTime(ks13_482) - 10, minf = 1, maxf = 10, event_index = 482)
    # stationCls['LD41'].PlotPick(start = UTCDateTime(ld41_482) - 10, minf = 1, maxf = 10, event_index = 482)
    # cat = pd.read_csv(os.path.join(Sta.workdir, 'catalogs_tomodd.csv'))
    # import json
    # with open('/mnt/ufs18/home-175/jieyaqi/code/EQDetection/TP.json', 'r') as f:
    #     mapper = json.load(f)
    # for k, v in mapper.items():
    #     picks_event = reloPicks[reloPicks['event_index'] == v]
    #     for i, row in picks_event.iterrows():
    #         stationCls[row['station']].PlotPick(start = UTCDateTime(row['timestamp']) - 10,
    #                 minf = 1, 
    #                 maxf = 10,
    #                 event_index = v)
    ################################## Calculate F-score ##################################
    # manager = mp.Manager()
    # lock = manager.Lock()
    # fscore_pre = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
    #                           's':{'TP': 0, 'FN': 0, 'FP':0},
    #                           'all': {'TP': 0, 'FN': 0, 'FP': 0},
    #                           'manual': {'p': 0, 's': 0},
    #                           'predict': {'p': 0, 's': 0}})
    
    # fscore_aso = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
    #                           's':{'TP': 0, 'FN': 0, 'FP':0},
    #                           'all': {'TP': 0, 'FN': 0, 'FP': 0},
    #                           'manual': {'p': 0, 's': 0},
    #                           'predict': {'p': 0, 's': 0}})

    # fscore_relo = manager.dict({'p':{'TP': 0, 'FN': 0, 'FP': 0}, 
    #                         's':{'TP': 0, 'FN': 0, 'FP':0},
    #                         'all': {'TP': 0, 'FN': 0, 'FP': 0},
    #                         'manual': {'p': 0, 's': 0},
    #                         'predict': {'p': 0, 's': 0}})
    
    # with mp.Pool(parameter['ncpu']) as p:
    #     p.starmap(Process, zip(stationCls.values(), repeat(lock), repeat(fscore_pre), repeat(fscore_aso), repeat(fscore_relo)))
    
    # precision_p = fscore_pre['p']['TP']/(fscore_pre['p']['TP']+fscore_pre['p']['FP'])
    # precision_s = fscore_pre['s']['TP']/(fscore_pre['s']['TP']+fscore_pre['s']['FP'])
    # precision_all = fscore_pre['all']['TP']/(fscore_pre['all']['TP']+fscore_pre['all']['FP'])
    # recall_p = fscore_pre['p']['TP']/(fscore_pre['p']['TP']+fscore_pre['p']['FN'])
    # recall_s = fscore_pre['s']['TP']/(fscore_pre['s']['TP']+fscore_pre['s']['FN'])
    # recall_all = fscore_pre['all']['TP']/(fscore_pre['all']['TP']+fscore_pre['all']['FN'])
    # print(dict(fscore_pre))
    # print(f'precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')

    # precision_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FP'])
    # precision_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FP'])
    # precision_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FP'])
    # recall_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FN'])
    # recall_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FN'])
    # recall_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FN'])
    # print(dict(fscore_aso))
    # print(f'ASSOCIATION precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')

    # precision_p = fscore_relo['p']['TP']/(fscore_relo['p']['TP']+fscore_relo['p']['FP'])
    # precision_s = fscore_relo['s']['TP']/(fscore_relo['s']['TP']+fscore_relo['s']['FP'])
    # precision_all = fscore_relo['all']['TP']/(fscore_relo['all']['TP']+fscore_relo['all']['FP'])
    # recall_p = fscore_relo['p']['TP']/(fscore_relo['p']['TP']+fscore_relo['p']['FN'])
    # recall_s = fscore_relo['s']['TP']/(fscore_relo['s']['TP']+fscore_relo['s']['FN'])
    # recall_all = fscore_relo['all']['TP']/(fscore_relo['all']['TP']+fscore_relo['all']['FN'])
    # print(dict(fscore_relo))
    # print(f'RELOCATION precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')
	
    # ################################## Plot waveforms for events ##################################
    # ev = Event(57.193,-160.193,401, UTCDateTime('2019-01-03T20:51:22.562000Z'), 811)
    # ev.Plot(stationCls, 0.5, 10, 1, 0, 4, True)