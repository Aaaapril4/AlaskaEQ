from obspy import UTCDateTime
from plot import PlotEvent
import os
from obspy.taup import TauPyModel

class Event:
    def __init__(self, lat: float, lon: float, depth: float, magnitude: float, otime: UTCDateTime) -> None:
        self.latitude = lat
        self.longitude = lon
        self.depth = depth
        self.magnitude = magnitude
        self.otime = otime



    def CalDist(self, stlat, stlon, olat = None, olon = None):
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
        if olat == None:
            result = client.distaz(stalat=stlat, stalon=stlon, evtlat=self.latitude, evtlon=self.longitude)
        else:
            result = client.distaz(stalat=stlat, stalon=stlon, evtlat=olat, evtlon=olon)

        return float(result['distance'])
        # return float(result['distancemeters']/1000, result['distance'])
    


    def Plot(self, stacls: dict, minf: float, amplifier: float, start: float, end: float):
        model = TauPyModel(model="PREM")
        eventData = {}
        figdir = os.path.join(self.workdir, 'figures', 'event')
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        for sta in stacls.values():
            edata = {}
            dist = self.CalDist(sta.latitude, sta.longitude)
            data, delta = sta.GetData(start = self.otime + start * 60, end = self.otime + end * 60, minf = minf)
            dpt, dst, mpt, mst = sta.GetPicks(start = self.otime - 2 * 60, end = self.otime + 5 * 60, delta = delta)
            
            for i, t in enumerate(dpt):
                dpt[i] = t * delta + start * 60
            for i, t in enumerate(dst):
                dst[i] = t * delta + start * 60
            for i, t in enumerate(mpt):
                mpt[i] = t * delta + start * 60
            for i, t in enumerate(mst):
                mst[i] = t * delta + start * 60

            arrivals = model.get_travel_times(source_depth_in_km=self.depth, distance_in_degree=dist, phase_list=['P', 'p', 'S', 's'])
            arrivalsl = {}
            for t in arrivals:
                if (t.phase.name.lower() == 'p') and ('p' not in arrivalsl.keys()):
                    arrivalsl['p'] = t.time
                elif (t.phase.name.lower() == 's') and ('s' not in arrivalsl.keys()):
                    arrivalsl['s'] = t.time

            edata['dpt'] = dpt
            edata['dst'] = dst
            edata['mpt'] = mpt
            edata['mst'] = mst
            edata['pos'] = [dist, amplifier]
            edata['theoryt'] = arrivalsl

            if data != None:
                edata['delta'] = delta
                for c, v in data.items():
                    if 'Z' in c:
                        edata['dataZ'] = v/max(v) * amplifier + dist
                    elif '1' in c or 'E' in c:
                        edata['dataE'] = v/max(v) * amplifier + dist
                    elif '2' in c or 'N' in c:
                        edata['dataN'] = v/max(v) * amplifier + dist
                eventData[sta.name] = edata

        fig_name = os.path.join(figdir, f'{self.otime.__unicode__()}_{self.latitude}_{self.longitude}_{self.depth}_{self.magnitude}')
        PlotEvent(eventData, fig_name, start, end)