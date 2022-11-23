from sta import Sta
import os
from obspy import UTCDateTime
import numpy as np
from event import Event
import multiprocessing as mp


def sort_manual_pick(mpickf: dict, etcol: int = 1, stacol: int = 7, arrivalcol: int = 9, phasecol: int = 10) -> None:
    '''
    Sort the phase picks into directory
    '''

    mpickdic = {}
    etime, sta, arrival, phase = np.loadtxt(mpickf, dtype = str, skiprows=1, usecols=(etcol, stacol, arrivalcol, phasecol),unpack=True)

    for i, t in enumerate(arrival):
        if sta[i] not in mpickdic.keys():
            mpickdic[sta[i]] = {'P':[], 'S':[]}
        
        if phase[i] == 'P':
            mpickdic[sta[i]]['P'].append(UTCDateTime(etime[i])+float(t))
        elif phase[i] == 'S':
            mpickdic[sta[i]]['S'].append(UTCDateTime(etime[i])+float(t))

    return mpickdic



def Process(stacls, manpicks):
    stacls.LoadPred()
    stacls.LoadProb()
    stacls.LoadManualPick(manpicks)
    stacls.CalFscore(1)
    stacls.PlotPick(minf = 1.5, maxf = 20, start = UTCDateTime(2018, 12, 1, 10, 30, 0), end = UTCDateTime(2018, 12, 1, 10, 55, 0))
    


if __name__ == '__main__':
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/test/'
    # Sta.workdir = '/mnt/ufs18/nodr/home/jieyaqi/alaska/test'
    Sta.parameter = {'p': 0.3, 's': 0.3, 'earthquake': 0.5, 'ncpu': 20}
    Event.workdir = '/mnt/scratch/jieyaqi/alaska/test/'
    Event.parameter = {'ncpu': 20}
    detdir = os.path.join(Sta.workdir, 'detections')
    stationjson = os.path.join(Sta.workdir, 'station_list.json')
    datadir = os.path.join(Sta.workdir, 'data')
    associatedir = os.path.join(Sta.workdir, 'association')
    model = os.path.join(Sta.workdir, "EqT_original_model.h5")
    start = UTCDateTime(year = 2018, month = 11, day = 1)
    end = UTCDateTime(year = 2019, month = 1, day = 3)

    if not os.path.isfile(stationjson):
        stationCls = Sta.GenJSON()
    else:
        stationCls = Sta.GenSta()

    if not os.path.isdir(detdir):
        from EQTransformer.core.mseed_predictor import mseed_predictor
        mseed_predictor(input_dir=datadir, 
            input_model=model, 
            stations_json=stationjson, 
            output_dir=detdir, 
            detection_threshold=Sta.parameter['earthquake'], 
            P_threshold=Sta.parameter['p'], 
            S_threshold=Sta.parameter['s'], 
            number_of_plots=0, 
            plot_mode='time', 
            overlap=0.3, 
            batch_size=500, 
            output_probabilities=True)

    if not os.path.isdir(os.path.join(Sta.workdir, 'figures')):
        os.makedirs(os.path.join(Sta.workdir, 'figures'))

    if not os.path.isdir(associatedir):
        os.makedirs(associatedir)

    manpicks = sort_manual_pick(os.path.join(Sta.workdir, 'manpick'))

    # for sta in stationCls.values():
    #     Process(sta, manpicks)
    # # Process(stationCls['AD07'], manpicks)
    with mp.Pool(Sta.parameter['ncpu']) as p:
        p.starmap(Process, zip(stationCls.values(), [manpicks] * len(stationCls)))
    # e = Event(lat = 56.4974, lon = -156.07, depth = 54.1, otime = UTCDateTime(2018,11,7,6,49,52,697), magnitude=2.7)
    # e.Plot(stationCls, minf = 0.5, maxf = 20, amplifier = 8, start = -2, end = 5)
    
    # ev = [['2018-12-04T17:23:14.743000Z', 54.639600, -160.874200, 33.600000], ['2018-12-04T17:28:48.797000Z', 55.292600, -160.672000, 48.300000], ['2018-12-04T17:29:40.648000Z', 58.176400, -155.308400, 3.300000]]
    # ev = [['2018-12-29T21:45:52.907000Z', 58.331100, -154.696500, 2.9], ['2018-12-29T21:46:09.605000Z', 58.334500, -154.665500, 1.5], ['2018-12-29T21:52:18.708000Z', 58.343500, -154.638800, 2.8]]
    # Event.PlotMultiEvent(ev, UTCDateTime(ev[0][0]), UTCDateTime(ev[0][0]) + 8*60, 58.3, -154.6, stationCls, 2, 20, 8)