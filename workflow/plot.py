import h5py
import random
from obspy import UTCDateTime
import obspy
import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import json

def PlotComponent(ax, com: str, data: dict, delta: float, ppt: list, mppt: list, pst: list, mpst: list, title: str):
    try:
        ax.plot(data[com], 'k', linewidth = 0.8)
    except:
        pass
    x = np.arange(60/delta)
    ax.set_xlim(0, 60/delta) 
    ymin, ymax = ax.get_ylim()
    ax.set_title(title)

    ax.set_ylabel('Amplitude\nCounts')
    ax.set_xticks(ticks=np.arange(0,60/delta+1, 10/delta))
    ax.set_xticklabels(np.arange(0,60+1, 10))
    
    pl = sl = mpl = msl = None        
    if len(ppt) > 0 and com != None:
        for ipt, pt in enumerate(ppt):
            if pt and ipt == 0:
                pl = ax.vlines(int(pt), ymin, ymax, color='c', linewidth=2, label='EQT P')
            elif pt and ipt > 0:
                pl = ax.vlines(int(pt), ymin, ymax, color='c', linewidth=2)
        
        for pt in mppt:
            mpl = ax.vlines(int(pt), ymin, ymax, color='orange', linestyles='dashed', linewidth=2)
    
    if len(pst) > 0 and com != None: 
        for ist, st in enumerate(pst): 
            if st and ist == 0:
                sl = ax.vlines(int(st), ymin, ymax, color='m', linewidth=2, label='EQT S')
            elif st and ist > 0:
                sl = ax.vlines(int(st), ymin, ymax, color='m', linewidth=2)
        
        for pt in mpst:
            msl = ax.vlines(int(pt), ymin, ymax, color='springgreen', linestyles='dashed', linewidth=2)
                
    if (pl or sl) and ( not msl and not mpl):    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        custom_lines = [Line2D([0], [0], color='k', lw=0),
                        Line2D([0], [0], color='c', lw=2),
                        Line2D([0], [0], color='m', lw=2)]
        ax.legend(custom_lines, [com, 'EQT P', 'EQT S'], 
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
        ax.legend(custom_lines, [com, 'EQT P', 'EQT S', 'AEC P', 'AEC S'], 
                    loc='center left', bbox_to_anchor=(1.01, 0.5), 
                    fancybox=True, shadow=True)

    

def PlotTime(figf: str, data: dict, mppt: list, mpst: list, ppt: list, pst: list, delta: float, yh1: list, yh2: list, yh3):
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
    fig = plt.figure(constrained_layout=True, figsize=(8,6))
    widths = [1]
    heights = [1.6, 1.6, 1.6, 2.5]
    spec = fig.add_gridspec(ncols=1, nrows=4, width_ratios=widths,
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
    ax = fig.add_subplot(spec[0, 0])
    PlotComponent(ax, come, data, delta, ppt, mppt, pst, mpst, figf.split("/")[-1])

    # plot N component                    
    ax = fig.add_subplot(spec[1, 0])
    PlotComponent(ax, comn, data, delta, ppt, mppt, pst, mpst, figf.split("/")[-1])
    
    # Plot Z component
    ax = fig.add_subplot(spec[2, 0]) 
    PlotComponent(ax, comz, data, delta, ppt, mppt, pst, mpst, figf.split("/")[-1])

    # Plot probability
    ax = fig.add_subplot(spec[3, 0])
    x = np.linspace(0, len(yh1), len(yh1), endpoint=True)
                        
    plt.plot(x, np.array(yh1), '--', color='g', alpha = 0.5, linewidth=1.5, label='Earthquake')
    plt.plot(x, np.array(yh2), '--', color='b', alpha = 0.5, linewidth=1.5, label='P_arrival')
    plt.plot(x, np.array(yh3), '--', color='r', alpha = 0.5, linewidth=1.5, label='S_arrival')
        
    plt.tight_layout()       
    plt.ylim((-0.1, 1.1)) 
    plt.xlim(0, 6000)
    plt.xticks(ticks=np.arange(0,6000+1, 1000), labels=np.arange(0,60+1, 10))                                 
    plt.ylabel('Probability') 
    plt.xlabel('Time')  
    legend_properties = {'weight':'bold'}     
    plt.legend(loc='lower center', bbox_to_anchor=(0., 1.17, 1., .102), ncol=3, mode="expand",
                    prop=legend_properties,  borderaxespad=0., fancybox=True, shadow=True)
    plt.yticks(np.arange(0, 1.1, step=0.2))
    axes = plt.gca()
    axes.yaxis.grid(color='lightgray')
        
    fig.tight_layout()
    fig.savefig(figf + '.pdf', format='pdf') 
    plt.close(fig)
    plt.clf()
    return



def cal_dist(stlat, stlon, evlat, evlon, type):
    '''
    Calculate the distance between station and event
    Input:
        stlat, stlon, evlat, evlon
        type: 'distance', 'backazimuth', 'azimuth'
    Return:
        result in km or degree
    '''
    
    from obspy.clients.iris import Client
    client = Client()
    result = client.distaz(stalat=stlat, stalon=stlon, evtlat=evlat, evtlon=evlon)

    return float(result[type])



def sort_trace_time(path):
    '''
    Return a dictionary of time of each trace
    Structure:
        trtime = {net.sta:{location: loc, channel: [], time: starttime-endtime}}
    '''
    trtime = {}
    for sta in os.listdir(path):
        for tr in os.listdir(f'{path}/{sta}'):
            [ net, sta, loc , time ] = tr.split('.')[0:4]
            [ cha, bt, et ] = time.split('__')

            if f'{net}.{sta}' not in trtime.keys():
                trtime[f'{net}.{sta}'] = {}
            
            if 'channel' not in trtime[f'{net}.{sta}'].keys():
                trtime[f'{net}.{sta}']['channel'] = []

            if 'time' not in trtime[f'{net}.{sta}'].keys():
                trtime[f'{net}.{sta}']['time'] = []

            trtime[f'{net}.{sta}']['location'] = loc
            trtime[f'{net}.{sta}']['channel'].append(cha)
            trtime[f'{net}.{sta}']['time'].append(f'{bt}__{et}')
            trtime[f'{net}.{sta}']['time'] = list(set(trtime[f'{net}.{sta}']['time']))
    return trtime



def get_offdata(path, trtime, evname, evlat, evlon, evtime, bw, ew, amp, cha):
    [ sta, net ] = evname.split('_')[0:2]
    stalat, stalon = get_sta_latlon(net, sta, stafile)
    dist = cal_dist(stalat, stalon, evlat, evlon, 'distance')
    stainfo = trtime[f'{net}.{sta}']
    for t in stainfo['time']:
        if evtime < UTCDateTime(t.split('__')[0]) or evtime > UTCDateTime(t.split('__')[1]):
            continue
        
        loc = stainfo['location']
        for c in stainfo['channel']:
            if c[2] == cha:
                channel = c
        st = obspy.read(f'{path}/{sta}/{net}.{sta}.{loc}.{channel}__{t}.mseed')
        print(f'{path}/{sta}/{net}.{sta}.{loc}.{channel}__{t}.mseed')
        for tr in st:
            if evtime < tr.stats.starttime or evtime > tr.stats.endtime:
                continue
            tr.filter('bandpass', freqmin = 1, freqmax = 45)
            ib = int((evtime - tr.stats.starttime - bw)/tr.stats.delta)
            ie = int((evtime - tr.stats.starttime + ew)/tr.stats.delta)
            evarr = tr.data[int(ib): int(ie)+1]
            evarr = evarr / max(evarr)
            break
        break
    return evarr + dist, tr.stats.delta



def plot_moveout(ass_dir):
    with open(f'{ass_dir}/traceNmae_dic.json') as f:
        evtr = json.load(f)
    ev = obspy.read_events(f'{path}/associations.xml')
    stafile = "/mnt/scratch/jieyaqi/alaska/station.txt"
    for evid in evtr.keys():
        if evid[0] != '2':
            continue

    evtrlist = evtr[evid]
    evinfo = ev[int(evid) - 200001].origins[0]
    evlat = evinfo.latitude
    evlon = evinfo.longitude
    evtime = evinfo.time
    print(evid)
    plt.figure(figsize=(5,10))
    for evname in evtrlist:
        data, dt = get_offdata(f'{path}/downloads_mseeds', trtime, evname, evlat, evlon, evtime, 2 * 60, 5 * 60, 2, 'Z')
        x = np.arange(-2*60, 5*60 + dt, dt)
        if len(x) != len(data):
            x = np.append(x, x[-1]+dt)
        plt.plot(x, data, color='black', linewidth=0.5)
        plt.xlim([-120,300])
        plt.ylim([-2,10])
    

if __name__ == '__main__':
    mpickdir = sort_manual_pick("/mnt/ufs18/nodr/home/jieyaqi/alaska/manual_pick/AACSE_arrival_final_PS.dat")
    plot_time("/mnt/scratch/jieyaqi/alaska/test/detections", "/mnt/scratch/jieyaqi/alaska/test/data", "/mnt/scratch/jieyaqi/alaska/test/figures", mpickdir = mpickdir, number_of_plots=20)