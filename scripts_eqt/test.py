from sta import Sta
import os
from obspy import UTCDateTime
import numpy as np
from event import Event
import multiprocessing as mp
from associate import Association


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
    stacls.SetID()
    # stacls.LoadPred()
    # stacls.LoadProb()
    # stacls.LoadManualPick(manpicks)
    # stacls.CalFscore(1)
    # stacls.PlotPick(minf = 1.5, maxf = 20, start = UTCDateTime('2018-12-29T21:46:09.605000Z'), end = UTCDateTime('2018-12-29T21:50:09.605000Z'))
    


if __name__ == '__main__':
    Sta.workdir = '/mnt/scratch/jieyaqi/alaska/test/'
    Sta.datadir = '/mnt/scratch/jieyaqi/alaska/waveform'
    # Sta.workdir = '/mnt/ufs18/nodr/home/jieyaqi/alaska/test'
    Sta.parameter = {'p': 0.3, 's': 0.3, 'earthquake': 0.5, 'ncpu': 20}
    Event.workdir = Sta.workdir
    Event.parameter = {'ncpu': 40}
    detdir = os.path.join(Sta.workdir, 'detections')
    stationjson = os.path.join(Sta.workdir, 'station_list.json')
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
        mseed_predictor(input_dir=Sta.datadir, 
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
    Association(stationCls)

    manpicks = sort_manual_pick('/mnt/ufs18/nodr/home/jieyaqi/alaska/manual_pick/AACSE_arrival_final_PS.dat')

    for sta in stationCls.values():
        Process(sta, manpicks)

    # Process(stationCls['AD07'], manpicks)
    # with mp.Pool(Sta.parameter['ncpu']) as p:
    #     p.starmap(Process, zip(stationCls.values(), [manpicks] * len(stationCls)))
    # e = Event(lat = 56.4974, lon = -156.07, depth = 54.1, otime = UTCDateTime(2018,11,7,6,49,52,697), magnitude=2.7)
    # e.Plot(stationCls, minf = 0.5, maxf = 20, amplifier = 8, start = -2, end = 5)


    # ev = [['2018-07-03T13:11:08.110000Z', 57.8147, -157.4748, 181.8], ['2018-07-03T13:14:03.409000Z', 57.0227, -157.9048, 6.4], ['2018-07-03T13:14:39.284000Z', 57.0462, -157.9138, 0.6], ['2018-07-03T13:15:37.829000Z', 57.0299, -157.9352, 6.1]]
    # ev = [['2018-07-03T13:10:57.975Z', 57.381054, -156.631388, 173.8], ['2018-07-03T13:10:59.430Z', 57.559745, -157.928308, 124.77], ['2018-07-03T13:13:19.868Z', 56.403366, -165.330413, 182.68],['2018-07-03T13:14:36.031', 57.071728, -157.869679, 63.4]]
    ev = [['2018-10-04T21:07:25.525000Z', 55.8117, -149.9031, 17.4], ['2018-10-04T21:07:38.887000Z', 55.7051, -149.7506, 15.2], ['2018-10-04T21:09:56.555000Z', 55.8112, -149.7632, 12.1], ['2018-10-04T21:12:19.770000Z', 55.8438, -149.6608, 12.2]]
    # ev = [['2018-12-29T21:45:52.907000Z', 58.331100, -154.696500, 2.9], ['2018-12-29T21:46:09.605000Z', 58.334500, -154.665500, 1.5], ['2018-12-29T21:52:18.708000Z', 58.343500, -154.638800, 2.8]]
    # event = ev[0]
    # Event.PlotMultiEvent(ev, UTCDateTime(ev[0][0]), UTCDateTime(ev[0][0]) + 6*60, 55, -149, stationCls, 2, 20, 8, True)