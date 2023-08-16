from sta import Sta
import os
from obspy import UTCDateTime
from event import Event
import pandas as pd
from obspy.clients.filesystem.tsindex import Client
import multiprocessing as mp
from itertools import repeat
import random



def Process(stacls, lock = None, fscoreall_pre = None, fscoreall_aso = None):
    fscore_pre, fscore_aso = stacls.CalFscoreSta(start = UTCDateTime(2019,1,1),
                        end = UTCDateTime(2019,3,1),
                        threshold = 1)
    
    # for i in range(5):
    #     if len(fscore_aso['p']['TP']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['TP']))
    #         stacls.PlotPick(start = t - 5,
    #                         minf = 2, 
    #                         maxf = 20)
    #     if len(fscore_aso['p']['FN']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['FN']))
    #         stacls.PlotPick(start = t - 5,
    #                         minf = 2, 
    #                         maxf = 20)
    #     if len(fscore_aso['p']['FP']) != 0:
    #         t = UTCDateTime(random.choice(fscore_aso['p']['FP']))
    #         stacls.PlotPick(start = t - 5,
    #                         minf = 2, 
    #                         maxf = 20)
        
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
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/eqt/'
    Event.workdir = Sta.workdir
    Sta.client = Client('/mnt/scratch/jieyaqi/alaska/phasenet/timeseries.sqlite')
    parameter = {'predict': {'p': 0.1, 's': 0.1, 'earthquake': 0.2}, 
                 'filter': {'p': 0.5, 's': 0.5}, 
                 'ncpu': 20}
    detdir = os.path.join(Sta.workdir, 'detections')
    stationjson = os.path.join(Sta.workdir, 'station_list.json')
    model = os.path.join(Sta.workdir, "EqT_original_model.h5")

    # Generate station instances
    if not os.path.isfile(stationjson):
        stationCls = Sta.GenJSON()
    else:
        stationCls = Sta.GenSta()

    # Do prediction if not
    if not os.path.isdir(detdir):
        from EQTransformer.core.mseed_predictor import mseed_predictor
        mseed_predictor(input_dir=Sta.datadir, 
            input_model=model, 
            stations_json=stationjson, 
            output_dir=detdir, 
            detection_threshold=parameter['predict']['earthquake'], 
            P_threshold=parameter['predict']['p'], 
            S_threshold=parameter['predict']['s'], 
            number_of_plots=0, 
            plot_mode='time', 
            overlap=0.3, 
            batch_size=500, 
            output_probabilities=True)

    # Prepare for ploting
    if not os.path.isdir(os.path.join(Sta.workdir, 'figures')):
        os.makedirs(os.path.join(Sta.workdir, 'figures'))

    # Process prediction result if not
    if not os.path.isfile(os.path.join(Sta.workdir, 'picks.csv')):
        prePicks = pd.read_csv(os.path.join(Sta.workdir, 'picks_raw.csv'))
        prePicksP = prePicks[["network", "station", "p_arrival_time", "p_probability"]]
        prePicksP = prePicksP[prePicksP['p_probability'] >= parameter['filter']['p']]
        prePicksP['type'] = 'P'
        prePicksP.columns = ["network", "station", "timestamp", "prob", "type"]

        prePicksS = prePicks[["network", "station", "s_arrival_time", "s_probability"]]
        prePicksS = prePicksS[prePicksS['s_probability'] >= parameter['filter']['s']]
        prePicksS['type'] = 'S'
        prePicksS.columns = ["network", "station", "timestamp", "prob", "type"]
        prePicks = pd.concat([prePicksP, prePicksS])
        prePicks['id'] = prePicks.apply(lambda x: f'{x["network"]}.{x["station"]}..BH'.replace(' ', ''), axis = 1)
        prePicks['timestamp'] = prePicks['timestamp'].apply(lambda x: 'T'.join(x.split(' ')))
        prePicks.to_csv(os.path.join(Sta.workdir, 'picks.csv'),
                        index=False, 
                        float_format="%.3f",
                        date_format='%Y-%m-%dT%H:%M:%S.%f')
    else:
        prePicks = pd.read_csv(os.path.join(Sta.workdir, 'picks.csv'))

    # process manual picks
    manPicks = pd.read_csv('data/manualPicks.csv')
    asoPicks = pd.read_csv(os.path.join(Sta.workdir, 'picks_gamma.csv'))

    Sta.manPicks = manPicks
    Sta.prePicks = prePicks
    Sta.asoPicks = asoPicks

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
    print(f'PREDICTION precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')
    
    precision_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FP'])
    precision_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FP'])
    precision_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FP'])
    recall_p = fscore_aso['p']['TP']/(fscore_aso['p']['TP']+fscore_aso['p']['FN'])
    recall_s = fscore_aso['s']['TP']/(fscore_aso['s']['TP']+fscore_aso['s']['FN'])
    recall_all = fscore_aso['all']['TP']/(fscore_aso['all']['TP']+fscore_aso['all']['FN'])
    print(dict(fscore_aso))
    print(f'ASSOCIATION precision: p-{precision_p}, s-{precision_s}, all-{precision_all}, recall: p-{recall_p}, s-{recall_s}, all-{recall_all}')

    # ev = Event(56.940,-152.612,11.959, UTCDateTime('2019-01-27T16:08:05.169'), 1)
    # ev.Plot(stationCls, 2, 20, 8, 0, 5)