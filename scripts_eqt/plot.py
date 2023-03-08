import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from obspy import UTCDateTime

def PlotComponent(ax, com: str, data: dict, delta: float, ppt: list, mppt: list, pst: list, mpst: list, title: str):
    try:
        ax.plot(data[com], 'k', linewidth = 0.8)
    except:
        pass
    ax.set_xlim(0, 60/delta) 
    ymin, ymax = ax.get_ylim()
    ax.set_title(title)

    ax.set_ylabel('Amplitude\nCounts')
    ax.set_xticks(ticks=np.arange(0,60/delta+1, 10/delta))
    ax.set_xticklabels(np.arange(0,60+1, 10))

    ax.vlines(ppt, [ymin]*len(ppt), [ymax]*len(ppt), color='c', linewidth=2, zorder = 5)
    ax.scatter(mppt, [0]*len(mppt), color='c', s = 15, zorder = 10)
    ax.vlines(pst, [ymin]*len(pst), [ymax]*len(pst), color='m', linewidth=2, zorder = 5)
    ax.scatter(mpst, [0]*len(mpst), color='m', s = 15, zorder = 10)
 
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    custom_lines = [Line2D([0], [0], color='k', lw=0),
                    Line2D([0], [0], color='c', lw=2),
                    Line2D([0], [0], color='m', lw=2),
                    Line2D([0], [0], color='c', marker = 'o', lw=0),
                    Line2D([0], [0], color='m', marker = 'o', lw=0)]
    ax.legend(custom_lines, [com, 'EQT P', 'EQT S', 'ACE P', 'ACE S'], 
                loc='center left', bbox_to_anchor=(1.01, 0.5), 
                fancybox=True, shadow=True)

    

def PlotTime(figf: str, data: dict, mppt: list, mpst: list, ppt: list, pst: list, delta: float, yh1: list, yh2: list, yh3: list):
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
    if yh1 != None: 
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



def PlotEvent(
    datadic: dict, 
    figf: str, 
    start: float, 
    end: float, 
    theoy: list, 
    theop: list, 
    theos: list, 
    width: float, 
    evt: list = None, 
    evy: list = None) -> None:

    def _plotCom(ax, x, data, pos, mpt, mst, dpt, dst):

        if len(x) != len(data):
            minlen = min(len(x), len(data))
            x = x[0: minlen]
            data = data[0: minlen]
        
        ax.plot(x, data, color='k', linewidth=0.04, zorder = 0)
        ax.vlines(dpt, pos[0] - pos[1], pos[0] + pos[1],  color='c', lw=0.8, zorder = 5)
        ax.vlines(dst, pos[0] - pos[1], pos[0] + pos[1],  color='m', lw=0.8, zorder = 5)
        ax.scatter(mpt, [pos[0]] * len(mpt) , s = 7,edgecolors = 'none', facecolors = 'c', marker = 'o', zorder = 10)
        ax.scatter(mst, [pos[0]] * len(mst), s = 7, edgecolors = 'none', facecolors = 'm', marker = 'P', zorder = 10)

        return ax

    plt.figure(figsize=(width,10))
    fig, (axZ, axN, axE) = plt.subplots(ncols=3)

    for st, data in datadic.items():

        x = np.arange(start*60, end*60 + data['delta'], data['delta'])
        if 'dataZ' in data.keys():
            axZ = _plotCom(axZ, x, data['dataZ'], data['pos'], data['mpt'], data['mst'], data['dpt'], data['dst'])

        if 'dataN' in data.keys():
            axN = _plotCom(axN, x, data['dataN'], data['pos'], data['mpt'], data['mst'], data['dpt'], data['dst'])

        if 'dataE' in data.keys():
            axE = _plotCom(axE, x, data['dataE'], data['pos'], data['mpt'], data['mst'], data['dpt'], data['dst'])

    for i in range(len(theop)):
        axZ.plot(theop[i], theoy[i], color = 'c', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        axZ.plot(theos[i], theoy[i], color = 'm', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        axN.plot(theop[i], theoy[i], color = 'c', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        axN.plot(theos[i], theoy[i], color = 'm', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        axE.plot(theop[i], theoy[i], color = 'c', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        axE.plot(theos[i], theoy[i], color = 'm', lw = 0.5, alpha = 0.8, zorder = 15, linestyle = '--')
        
    if evt != None:
        axZ.scatter(evt, evy, s = 5, c = 'red', alpha = 0.8, marker = '*', zorder = 15)
        axE.scatter(evt, evy, s = 5, c = 'red', alpha = 0.8, marker = '*', zorder = 15)
        axN.scatter(evt, evy, s = 5, c = 'red', alpha = 0.8, marker = '*', zorder = 15)

    axZ.set_title('Z component', fontsize=8)
    axN.set_title('N component', fontsize=8)
    axE.set_title('E component', fontsize=8)

    axZ.set_xlim(start * 60, end * 60)
    axN.set_xlim(start * 60, end * 60) 
    axE.set_xlim(start * 60, end * 60)
    axZ.set_ylim(bottom=0)
    axN.set_ylim(bottom=0)
    axE.set_ylim(bottom=0)
    
    axZ.set_ylabel('Distance (km)', fontsize=8)
    axZ.set_xlabel('Time (s)', fontsize=8)
    axE.set_xlabel('Time (s)', fontsize=8)
    axN.set_xlabel('Time (s)', fontsize=8)
    axN.set_yticks([])
    axE.set_yticks([])
    axZ.tick_params(labelsize=8)
    axN.tick_params(labelsize=8)
    axE.tick_params(labelsize=8)

    custom_lines = [Line2D([0], [0], color='c', lw=0.8),
                    Line2D([0], [0], color='m', lw=0.8),
                    Line2D([0], [0], color='c', lw=0.8, linestyle='dashed'),
                    Line2D([0], [0], color='m', lw=0.8, linestyle='dashed')]
    fig.legend(custom_lines, ['EQT P', 'EQT S', 'AEC P', 'AEC S'], 
                loc='lower center', bbox_to_anchor=(1.01, 0.5), 
                fancybox=True, shadow=True, mode='expand')


    fig.tight_layout()
    plt.savefig(figf + '.pdf', format='pdf')
    plt.close(fig)
    plt.clf()



def PlotAllEvents(file):
    id, t, lo, la, d, m = np.loadtxt(file, unpack=True, usecols=(0, 1, 2, 3, 4, 5), dtype=str)
    nid = []
    nt = []
    nlo = []
    nla = []
    nd = []
    nm = []
    tdiff = []

    for i, idx in enumerate(id):
        if idx in nid:
            continue
        
        # generate new event table
        nid.append(idx)
        nt.append(t[i])
        nlo.append(float(lo[i]))
        nla.append(float(la[i]))
        nd.append(float(d[i]))
        nm.append(float(m[i]))
        tdiff.append((UTCDateTime(t[i]) - UTCDateTime(2018, 11, 1))/(24*60*60))

    id, t, lo, la, d, m, diff = zip(*sorted(zip(nid, nt, nlo, nla, nd, nm, tdiff)))

    start = t[0]
    temp = []
    for i, idx in enumerate(id):
        if i >= 1 and UTCDateTime(t[i]) - UTCDateTime(start) <= 480:
            temp.append(t[i])
        else:
            if len(temp) >= 2:
                print(temp)
            start = t[i]
            temp = [start]

    plt.figure(figsize=(4,3))
    plt.scatter(x = tdiff, y = nm, c = nd, s = 0.5, cmap='magma', vmin = 0, vmax = 220)
    plt.xlim([0,61])
    plt.xlabel('Time (day)', fontsize = 8)
    plt.ylabel('Magnitude', fontsize = 8)
    plt.xticks(fontsize = 8)
    plt.yticks(fontsize = 8)
    cbar = plt.colorbar()
    cbar.ax.tick_params(labelsize=8)
    plt.tight_layout()
    plt.savefig('/mnt/home/jieyaqi/Downloads/events.pdf', format = 'pdf')



if __name__ == "__main__":
    PlotAllEvents('/mnt/ufs18/nodr/home/jieyaqi/alaska/manual_pick/AACSE/test')