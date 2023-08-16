import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from obspy import UTCDateTime

def PlotComponent(
        ax, 
        com: str, 
        data: np.ndarray, 
        delta: float, 
        pickspt: dict,
        title: str,
        source: str,
        duration: int = 60):

    ax.plot(data, 'k', linewidth = 0.8)

    ax.set_xlim(0, duration/delta + 1) 
    ymin, ymax = ax.get_ylim()
    ax.set_title(title)

    ax.set_ylabel('Amplitude\nCounts')
    ax.set_xticks(ticks=np.linspace(0,duration/delta+1, 6, dtype=int))
    ax.set_xticklabels(np.linspace(0,duration, 6, dtype=int))

    if len(pickspt['pp']) != 0:
        ax.vlines(pickspt['pp'], [ymin]*len(pickspt['pp']), [ymax]*len(pickspt['pp']), color='c', linewidth=2, zorder = 5)
    if len(pickspt['mp']) != 0:
        ax.scatter(pickspt['mp'], [0]*len(pickspt['mp']), color='c', marker='X', s = 50, zorder = 10)
    if len(pickspt['ps']) != 0:
        ax.vlines(pickspt['ps'], [ymin]*len(pickspt['ps']), [ymax]*len(pickspt['ps']), color='m', linewidth=2, zorder = 5)
    if len(pickspt['ms']) != 0:
        ax.scatter(pickspt['ms'], [0]*len(pickspt['ms']), color='m', marker='X', s = 50, zorder = 10)
 
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    custom_lines = [Line2D([0], [0], color='k', lw=0),
                    Line2D([0], [0], color='c', lw=2),
                    Line2D([0], [0], color='m', lw=2),
                    Line2D([0], [0], color='c', marker = 'X', lw=0),
                    Line2D([0], [0], color='m', marker = 'X', lw=0)]
    ax.legend(custom_lines, [com, f'{source} P', f'{source} S', 'ACE P', 'ACE S'], 
                loc='center left', bbox_to_anchor=(1.01, 0.5), 
                fancybox=True, shadow=True)

    

def PlotTime(figf: str, 
             data: dict, 
             pickspt: dict, 
             delta: float,
             prob: dict,
             source: str,
             duration: int = 60):
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
    PlotComponent(ax, come, data[come], delta, pickspt, figf.split("/")[-1], source, duration)

    # plot N component                    
    ax = fig.add_subplot(spec[1, 0])
    PlotComponent(ax, comn, data[comn], delta, pickspt, figf.split("/")[-1], source, duration)
    
    # Plot Z component
    ax = fig.add_subplot(spec[2, 0]) 
    PlotComponent(ax, comz, data[comz], delta, pickspt, figf.split("/")[-1], source, duration)

    # Plot probability
    ax = fig.add_subplot(spec[3, 0])
    x = np.linspace(0, len(prob['p']), len(prob['p']), endpoint=True, dtype=int)
    plt.plot(x, np.array(prob['p']), '--', color='b', alpha = 0.5, linewidth=1.5, label='P_arrival')
    plt.plot(x, np.array(prob['s']), '--', color='r', alpha = 0.5, linewidth=1.5, label='S_arrival')
    if 'eq' in prob.keys():
        plt.plot(x, np.array(prob['eq']), '--', color='g', alpha = 0.5, linewidth=1.5, label='Earthquake')
        
    plt.tight_layout()       
    plt.ylim((-0.1, 1.1)) 
    plt.xlim(0, len(prob['p']))
    plt.xticks(ticks=np.linspace(0,len(prob['p']), 6, dtype=int), labels=np.linspace(0,duration, 6, dtype=int))                                 
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



def PlotTimePNTF(figf: str, 
             data: dict, 
             sgrams: dict,
             vmax: dict,
             pickspt: dict, 
             delta: float,
             prob: dict,
             source: str,
             freq_range: list,
             duration: int = 60):
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
    def PlotWaveform(
        ax, 
        com: str, 
        data: np.ndarray, 
        delta: float, 
        pickspt: dict,
        duration: int = 60):

        ax.plot(data, 'k', linewidth = 0.8)

        ax.set_ylim([-1,1])
        ax.set_yticks(np.arange(-1, 1.1, step=0.5))
        ax.set_yticklabels([])
        ax.set_ylabel('Amplitude')
        ax.text(4, 0.8, com)

        if len(pickspt['pp']) != 0:
            ax.vlines(pickspt['pp'], [-1]*len(pickspt['pp']), [1]*len(pickspt['pp']), color='c', linewidth=2, zorder = 5)
        if len(pickspt['mp']) != 0:
            ax.scatter(pickspt['mp'], [0]*len(pickspt['mp']), color='c', marker='X', s = 50, zorder = 10)
        if len(pickspt['ps']) != 0:
            ax.vlines(pickspt['ps'], [-1]*len(pickspt['ps']), [1]*len(pickspt['ps']), color='m', linewidth=2, zorder = 5)
        if len(pickspt['ms']) != 0:
            ax.scatter(pickspt['ms'], [0]*len(pickspt['ms']), color='m', marker='X', s = 50, zorder = 10)
    
    def PlotSpectogram(
        ax, 
        com: str, 
        data: np.ndarray,
        vmax: float, 
        delta: float, 
        pickspt: dict,
        duration: int = 60):

        ax.imshow(data,
                 aspect='auto',
                 cmap='jet',
                 origin='lower',
                 vmax = vmax,
                 extent=[0,duration*40] + freq_range)
        ax.set_ylabel('Frequency (Hz)')
        

    fig, ax = plt.subplots(7,1, sharex=True, figsize=(12, 18))    
    come = comn = comz = None
    for c in data.keys():
        if c[2] == 'E' or c[2] == '1':
            come = c
        elif c[2] == 'N' or c[2] == '2':
            comn = c
        elif c[2] == 'Z':
            comz = c

    # plot E component
    PlotWaveform(ax[0], come, data[come], delta, pickspt, duration)
    PlotSpectogram(ax[1], come, sgrams[come][0], vmax[come], delta, pickspt, duration)

    # plot N component                    
    PlotWaveform(ax[2], comn, data[comn], delta, pickspt, duration)
    PlotSpectogram(ax[3], comn, sgrams[comn][0], vmax[comn], delta, pickspt, duration)
    
    # Plot Z component
    PlotWaveform(ax[4], comz, data[comz], delta, pickspt, duration)
    PlotSpectogram(ax[5], comz, sgrams[comz][0], vmax[comz], delta, pickspt, duration)

    # Plot probability
    x = np.linspace(0, len(prob['p']), len(prob['p']), endpoint=True, dtype=int)
    ax[6].plot(x, np.array(prob['p']), '--', color='b', alpha = 0.5, linewidth=1.5, label='P_arrival')
    ax[6].plot(x, np.array(prob['s']), '--', color='r', alpha = 0.5, linewidth=1.5, label='S_arrival')
    if 'eq' in prob.keys():
        ax[6].plot(x, np.array(prob['eq']), '--', color='g', alpha = 0.5, linewidth=1.5, label='Earthquake')
    ax[6].set_ylim((-0.1, 1.1)) 
    ax[6].set_ylabel('Probability') 
    ax[6].set_yticks(np.arange(0, 1.1, step=0.2))
    ax[6].set_xlabel('Time (s)')

    custom_lines = [Line2D([0], [0], color='c', lw=2),
        Line2D([0], [0], color='m', lw=2),
        Line2D([0], [0], color='c', marker = 'X', lw=0),
        Line2D([0], [0], color='m', marker = 'X', lw=0),
        Line2D([0], [0], color='b', lw=1.5, ls='--'),
        Line2D([0], [0], color='r', lw=1.5, ls='--')]
    ax[6].legend(custom_lines, [f'PN-TF P', f'PN-TF S', 'ACE P', 'ACE S', 'P Arrival', 'S Arrival'], 
        loc=0)
    
    ax[0].set_xticks(ticks=np.linspace(0,duration/delta+1, 6, dtype=int))
    ax[0].set_xticklabels(np.linspace(0,duration, 6, dtype=int))
    ax[0].set_xlim(0, duration/delta + 1)
    ax[0].set_title(figf.split('/')[-1])
        
    plt.subplots_adjust(hspace=0)
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
    evt: list = None, 
    evy: list = None) -> None:

    def _plotCom(ax, data, pos, pickspt):
        
        ax.plot(data, color='k', linewidth=0.01, zorder = 0)

        ax.vlines(pickspt['pp'], pos[0] - pos[1], pos[0] + pos[1],  color='c', lw=1.5, zorder = 5, alpha=0.4)
        ax.vlines(pickspt['ps'], pos[0] - pos[1], pos[0] + pos[1],  color='m', lw=1.5, zorder = 5, alpha=0.4)

        ax.vlines(pickspt['ap'], pos[0] - pos[1], pos[0] + pos[1],  color='c', lw=1.5, zorder = 5)
        ax.vlines(pickspt['as'], pos[0] - pos[1], pos[0] + pos[1],  color='m', lw=1.5, zorder = 5)
        
        ax.scatter(pickspt['mp'], [pos[0]] * len(pickspt['mp']) , s = 20,edgecolors = 'none', facecolors = 'c', marker = 'X', zorder = 10)
        ax.scatter(pickspt['ms'], [pos[0]] * len(pickspt['ms']), s = 20, edgecolors = 'none', facecolors = 'm', marker = 'X', zorder = 10)

        return ax

    fig, (axZ, axN, axE) = plt.subplots(ncols=3, figsize=(20, 30))

    for st, dataSta in datadic.items():
        delta = dataSta['delta']
        for k, d in dataSta['data'].items():
            if 'Z' in k:
                axZ = _plotCom(axZ, d, dataSta['pos'], dataSta['picks'])

            if 'N' in k or '2' in k:
                axN = _plotCom(axN, d, dataSta['pos'], dataSta['picks'])

            if 'E' in k or '1' in k:
                axE = _plotCom(axE, d, dataSta['pos'], dataSta['picks'])

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

    duration = (end - start) * 60
    axZ.set_xlim(0, duration / delta + 1)
    axN.set_xlim(0, duration / delta + 1) 
    axE.set_xlim(0, duration / delta + 1)
    
    axZ.set_xticks(ticks=np.linspace(0, duration / delta + 1, 6, dtype=int))
    axZ.set_xticklabels(np.linspace(start * 60, end * 60 + 1, 6, dtype=int))
    axN.set_xticks(ticks=np.linspace(0, duration / delta + 1, 6, dtype=int))
    axN.set_xticklabels(np.linspace(start * 60, end * 60 + 1, 6, dtype=int))
    axE.set_xticks(ticks=np.linspace(0, duration / delta + 1, 6, dtype=int))
    axE.set_xticklabels(np.linspace(start * 60, end * 60 + 1, 6, dtype=int))
    
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