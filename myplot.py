import h5py
import random
from obspy import UTCDateTime
import obspy
import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def sort_manual_pick(mpickf, etcol=1, stacol=7, arrivalcol=9, phasecol=10):
    '''
    Sort the phase picks into directory
    Parameters
    ---------
    mpickf: str
        path to the text file of arrivals
    
    etcol, stacol, arrivalcol, phasecol: int
        column number of eventtime, station, arrival time, phase
    
    Return
    ------
    mpickdir: dict
        mpickdir = { sta: { P: [], S: [] } }
    '''

    mpickdir = {}
    etime, sta, arrival, phase = np.loadtxt(mpickf, dtype = str, skiprows=1, usecols=(etcol, stacol, arrivalcol, phasecol),unpack=True)

    for i in range(len(arrival)):
        if sta[i] not in mpickdir.keys():
            mpickdir[sta[i]] = {'P':[], 'S':[]}
        
        if phase[i] == 'P':
            mpickdir[sta[i]]['P'].append(obspy.core.utcdatetime.UTCDateTime(etime[i])+float(arrival[i]))
        elif phase[i] == 'S':
            mpickdir[sta[i]]['S'].append(obspy.core.utcdatetime.UTCDateTime(etime[i])+float(arrival[i]))

    return mpickdir



def _plot_time(fig_name, data, mppt, mpst, ppt, pst, delta, yh1, yh2, yh3):
    '''
    Plot picked phases (and manual picks) in time domain

    Parameters
    ----------
    fig_name: str
        Absolute path of figure
    data: dic
        Dictionary of data in three channels
    mppt, mpst, ppt, pst: list
        Manual picked P arrival, manual picked S arrival, predicted P arrival, predicted S arrival
    '''
    fig = plt.figure(constrained_layout=True)
    widths = [1]
    heights = [1.6, 1.6, 1.6, 2.5]
    spec5 = fig.add_gridspec(ncols=1, nrows=4, width_ratios=widths,
                            height_ratios=heights)
    
    come = comn = comz = None
    for c in data.keys():
        if c[2] == 'E' or c[2] == '1':
            come = c
        elif c[2] == 'N' or c[2] == '2':
            comn = c
        elif c[2] == 'Z':
            comz = c

    # plot E component
    ax = fig.add_subplot(spec5[0, 0])         
    try:
        plt.plot(data[come], 'k')
    except:
        pass
    x = np.arange(60/delta)
    plt.xlim(0, 60/delta) 
    ymin, ymax = ax.get_ylim()
    plt.title(fig_name.split("/")[-1])

    plt.ylabel('Amplitude\nCounts')
    plt.xticks(ticks=np.arange(0,60/delta+1, 10/delta), labels=np.arange(0,60+1, 10))

    plt.rcParams["figure.figsize"] = (8,6)
    legend_properties = {'weight':'bold'}
    
    pl = sl = mpl = msl = None        
    if len(ppt) > 0 and come != None:
        for ipt, pt in enumerate(ppt):
            if pt and ipt == 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2, label='Picked P')
            elif pt and ipt > 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2)
        
        for pt in mppt:
            mpl = plt.vlines(int(pt), ymin, ymax, color='orange', linestyles='dashed', linewidth=2)
    
    if len(pst) > 0 and come != None: 
        for ist, st in enumerate(pst): 
            if st and ist == 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2, label='Picked S')
            elif st and ist > 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2)
        
        for pt in mpst:
            msl = plt.vlines(int(pt), ymin, ymax, color='springgreen', linestyles='dashed', linewidth=2)
                
    if (pl or sl) and ( not msl and not mpl):    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2)]
        plt.legend(custom_lines, ['E', 'Picked P', 'Picked S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    if (pl or sl) and ( msl or mpl):    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2),
                        Line2D([0], [0], color='orange', lw=2, linestyle='dashed'),
                        Line2D([0], [0], color='springgreen', lw=2, linestyle='dashed')]
        plt.legend(custom_lines, ['E', 'Picked P', 'Picked S', 'Manual pick P', 'Manual pick S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    # plot N component                    
    ax = fig.add_subplot(spec5[1, 0])
    try: 
        plt.plot(data[comn] , 'k')
    except:
        pass
    plt.xlim(0, 60/delta)            
    plt.ylabel('Amplitude\nCounts')            
    plt.xticks(ticks=np.arange(0,60/delta+1, 10/delta), labels=np.arange(0,60+1, 10))
    ymin, ymax = ax.get_ylim()
    if len(ppt) > 0 and comn != None:
        for ipt, pt in enumerate(ppt):
            if pt and ipt == 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2, label='Picked P')
            elif pt and ipt > 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2)
        
        for pt in mppt:
            mpl = plt.vlines(int(pt), ymin, ymax, color='orange', linestyles='dashed', linewidth=2)
                
    if len(pst) > 0 and comn != None:
        for ist, st in enumerate(pst): 
            if st and ist == 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2, label='Picked S')
            elif st and ist > 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2)
        
        for pt in mpst:
            msl = plt.vlines(int(pt), ymin, ymax, color='springgreen', linestyles='dashed', linewidth=2)

    if (pl or sl) and ( not msl and not mpl): 
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2)]
        plt.legend(custom_lines, ['N', 'Picked P', 'Picked S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    if (pl or sl) and ( msl or mpl):    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2),
                        Line2D([0], [0], color='orange', lw=2, linestyle='dashed'),
                        Line2D([0], [0], color='springgreen', lw=2, linestyle='dashed')]
        plt.legend(custom_lines, ['E', 'Picked P', 'Picked S', 'Manual pick P', 'Manual pick S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    # Plot Z component
    ax = fig.add_subplot(spec5[2, 0]) 
    plt.plot(data[comz], 'k') 
    plt.xlim(0, 60/delta)                    
    plt.ylabel('Amplitude\nCounts')
    
    ax.set_xticks([])
    ymin, ymax = ax.get_ylim()

    if len(ppt) > 0 and comz != None:    
        for ipt, pt in enumerate(ppt):
            if pt and ipt == 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2, label='Picked P')
            elif pt and ipt > 0:
                pl = plt.vlines(int(pt), ymin, ymax, color='c', linewidth=2)
    
        for pt in mppt:
            mpl = plt.vlines(int(pt), ymin, ymax, color='orange', linestyles='dashed', linewidth=2)
                
    if len(pst) > 0 and comz != None:
        for ist, st in enumerate(pst): 
            if st and ist == 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2, label='Picked S')
            elif st and ist > 0:
                sl = plt.vlines(int(st), ymin, ymax, color='m', linewidth=2)

        for pt in mpst:
            msl = plt.vlines(int(pt), ymin, ymax, color='springgreen', linestyles='dashed', linewidth=2)
                
    if (pl or sl) and ( not msl and not mpl):       
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2)]
        plt.legend(custom_lines, ['Z', 'Picked P', 'Picked S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)       

    if (pl or sl) and ( msl or mpl):    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2),
                        Line2D([0], [0], color='orange', lw=2, linestyle='dashed'),
                        Line2D([0], [0], color='springgreen', lw=2, linestyle='dashed')]
        plt.legend(custom_lines, ['E', 'Picked P', 'Picked S', 'Manual pick P', 'Manual pick S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    ax = fig.add_subplot(spec5[3, 0])
    x = np.linspace(0, len(yh1), len(yh1), endpoint=True)
                        
    plt.plot(x, yh1, '--', color='g', alpha = 0.5, linewidth=1.5, label='Earthquake')
    plt.plot(x, yh2, '--', color='b', alpha = 0.5, linewidth=1.5, label='P_arrival')
    plt.plot(x, yh3, '--', color='r', alpha = 0.5, linewidth=1.5, label='S_arrival')
        
    plt.tight_layout()       
    plt.ylim((-0.1, 1.1)) 
    plt.xlim(0, 6000)
    plt.xticks(ticks=np.arange(0,6000+1, 1000), labels=np.arange(0,60+1, 10))                                 
    plt.ylabel('Probability') 
    plt.xlabel('Time')  
    plt.legend(loc='lower center', bbox_to_anchor=(0., 1.17, 1., .102), ncol=3, mode="expand",
                    prop=legend_properties,  borderaxespad=0., fancybox=True, shadow=True)
    plt.yticks(np.arange(0, 1.1, step=0.2))
    axes = plt.gca()
    axes.yaxis.grid(color='lightgray')
        
    font = {'family': 'serif',
                'color': 'dimgrey',
                'style': 'italic',
                'stretch': 'condensed',
                'weight': 'normal',
                'size': 12,
                }

    plt.text(6500, 0.5, 'EQTransformer', fontdict=font)
        
    fig.tight_layout()
    fig.savefig(fig_name + '.png') 
    plt.close(fig)
    plt.clf()
    return



def plot_time(inputdir, datadir, outdir, mpickdir, number_of_plots=10):
    '''
    Plot waveform and P and S arrivals in time domain

    Parameters
    ----------
    inputdir: str
        path to the detection result directory
    datadir: str
        path to the data directory
    number_of_plots: int
        number of plotting figures for each statioin
    '''

    stationlist = os.listdir(inputdir)
    if os.path.isdir(outdir) == True:
        shutil.rmtree(outdir)  
    os.makedirs(outdir) 

    for sta in stationlist:
        sta_name = sta.split('_')[0]
        stadir = os.path.join(inputdir, sta)
        if os.path.isdir(os.path.join(outdir, sta_name)) == False:
            os.mkdir(os.path.join(outdir, sta_name))

        # Load probability        
        prob_file = os.path.join(stadir, "prediction_probabilities.hdf5")
        PROB = h5py.File(prob_file, 'r')
        timeslot = list(PROB.keys())
        if len(timeslot) < number_of_plots:
            plot_index = list(range(timeslot))
        else:
            plot_index = random.sample(range(len(timeslot)), number_of_plots)
        
        # Load prediction
        pred_file = os.path.join(stadir, "X_prediction_results.csv")
        eventt, parrival, sarrival = np.loadtxt(pred_file, unpack = True, dtype = str, delimiter = ',', usecols = (7, 11, 15), skiprows=1)
        t_event = [''] * len(eventt)
        t_parrival = [''] * len(eventt)
        t_sarrival = [''] * len(eventt)
        for i in range(len(eventt)):
            if eventt[i] != '':
                t_event[i] = UTCDateTime('T'.join(eventt[i].split(' ')))
            if parrival[i] != '':
                t_parrival[i] = UTCDateTime('T'.join(parrival[i].split(' ')))
            if sarrival[i] != '':
                t_sarrival[i] = UTCDateTime('T'.join(sarrival[i].split(' ')))

        # Load data file
        data_time = {}
        for f in os.listdir(os.path.join(datadir, sta_name)):
            st = f.split('__')[1]
            cha = f.split('__')[0].split('.')[-1]
            if st not in data_time.keys():
                data_time[st] = {}
            if cha not in data_time[st].keys():
                data_time[st][cha] = f
                        
        for ix in plot_index:
            starttime = UTCDateTime(timeslot[ix])
            endtime = starttime + 60
            mppt = []
            mpst = []
            ppt = []
            pst = []

            # Get data
            data = {}
            for t in data_time.keys():
                if starttime >= UTCDateTime(t) and endtime <= UTCDateTime(t) + 60 * 60 * 24 * 30:
                    for c in data_time[t].keys():
                        tempstream = obspy.read(os.path.join(datadir, sta_name, data_time[t][c]))
                        for tr in tempstream:
                            if starttime >= tr.stats.starttime and starttime <= tr.stats.endtime:
                                tr.detrend('demean')
                                tr.filter(type='bandpass', freqmin = 1.0, freqmax = 45, corners=2, zerophase=True)
                                tr.taper(max_percentage=0.001, type='cosine', max_length=2) 
                                delta = tr.stats.delta
                                be = int((starttime - tr.stats.starttime) / delta)
                                ne = int((starttime - tr.stats.starttime + 60) / delta)
                                data[c] = tr.data[be:ne+1]
                                break

            # Find manual pick in the time interval
            if sta_name in mpickdir.keys():
                for man_p in mpickdir[sta_name]['P']:
                    if man_p >= starttime and man_p <= endtime:
                        mppt.append((man_p - starttime) / delta)
                for man_p in mpickdir[sta_name]['S']:
                    if man_p >= starttime and man_p <= endtime:
                        mpst.append((man_p - starttime) / delta)

            # Find predict arrival in the time interval
            for p in t_parrival:
                if p == '':
                    continue
                if p >= starttime and p <= endtime:
                    ppt.append((p - starttime) / delta)
            for s in t_sarrival:
                if s == '':
                    continue
                if s >= starttime and s <= endtime:
                    pst.append((s - starttime) / delta)

            fig_name = os.path.join(outdir, sta_name, f'{sta_name}:{timeslot[ix]}')
            _plot_time(fig_name, data, mppt, mpst, ppt, pst, delta, PROB[timeslot[ix]]['Earthquake'], PROB[timeslot[ix]]['P_arrival'], PROB[timeslot[ix]]['S_arrival'])

mpickdir = sort_manual_pick("/mnt/ufs18/nodr/home/jieyaqi/alaska/manual_pick/AACSE_arrival_final_PS.dat")
plot_time("/mnt/ufs18/nodr/home/jieyaqi/alaska/detections_test", "/mnt/ufs18/nodr/home/jieyaqi/alaska/test_month", "/mnt/ufs18/nodr/home/jieyaqi/alaska/figures", mpickdir = mpickdir, number_of_plots=50)