from obspy import UTCDateTime
from plot import PlotEvent
import os
from obspy.taup import TauPyModel
from obspy.clients.iris import Client
client = Client()
_CalDist = lambda sla, slo, ola, olo: client.distaz(stalat=sla, stalon=slo, evtlat=ola, evtlon=olo)


class Event:
    def __init__(self, lat: float, lon: float, depth: float, magnitude: float, otime: UTCDateTime) -> None:
        self.latitude = lat
        self.longitude = lon
        self.depth = depth
        self.magnitude = magnitude
        self.otime = otime



    def CalDist(self, stlat, stlon):
        '''
        Calculate the distance between station and event
        Input:
            stlat, stlon, evlat, evlon
            type: 'distance', 'backazimuth', 'azimuth'
        Return:
            result in km or degree
        '''
        result = _CalDist(stlat, stlon, self.latitude, self.longitude)
        # from obspy.clients.iris import Client
        # client = Client()
        # if olat == None:
        #     result = client.distaz(stalat=stlat, stalon=stlon, evtlat=self.latitude, evtlon=self.longitude)
        # else:
        #     result = client.distaz(stalat=stlat, stalon=stlon, evtlat=olat, evtlon=olon)

        # return float(result['distance'])
        return [float(result['distancemeters']/1000), float(result['distance'])]
    


    def Plot(self, stacls: dict, minf: float, maxf: float, amplifier: float, start: float, end: float, order: bool = False):
        model = TauPyModel(model="PREM")
        eventData = {}
        figdir = os.path.join(self.workdir, 'figures', 'event')
        
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        distd = {}
        for sta in stacls.values():
            distd[sta.name] = self.CalDist(sta.latitude, sta.longitude)
        distd = {k: v for k, v in sorted(distd.items(), key=lambda x: x[1][0])}

        theoy = []
        theop = []
        theos = []

        # for sta in stacls.values():
        for num, st in enumerate(distd.keys()):
            sta = stacls[st]
            dist = distd[st]
            edata = {}
            if order:
                y = num
            else:
                y = dist[0]
            # dist = self.CalDist(sta.latitude, sta.longitude)
            
            data, delta = sta.GetData(start = self.otime + start * 60, end = self.otime + end * 60, minf = minf, maxf = maxf)
            if delta == 0:
                continue
            dpt, dst, mpt, mst = sta.GetPicks(start = self.otime + start * 60, end = self.otime + end * 60, delta = delta)
            
            for i, t in enumerate(dpt):
                dpt[i] = t * delta + start * 60
            for i, t in enumerate(dst):
                dst[i] = t * delta + start * 60
            for i, t in enumerate(mpt):
                mpt[i] = t * delta + start * 60
            for i, t in enumerate(mst):
                mst[i] = t * delta + start * 60

            arrivals = model.get_travel_times(source_depth_in_km=self.depth, distance_in_degree=dist[1], phase_list=['P', 'p', 'S', 's'])
            p = 0
            s = 0
            theoy.append(y)
            for t in arrivals:
                if (t.phase.name.lower() == 'p') and (p == 0):
                    theop.append(t.time)
                    p = 1
                elif (t.phase.name.lower() == 's') and (s == 0):
                    theos.append(t.time)
                    s = 1

            edata['dpt'] = dpt
            edata['dst'] = dst
            edata['mpt'] = mpt
            edata['mst'] = mst
            edata['pos'] = [y, amplifier]

            if data != None:
                edata['delta'] = delta
                for c, v in data.items():
                    if 'Z' in c:
                        edata['dataZ'] = v/max(v) * amplifier + y
                    elif '1' in c or 'E' in c:
                        edata['dataE'] = v/max(v) * amplifier + y
                    elif '2' in c or 'N' in c:
                        edata['dataN'] = v/max(v) * amplifier + y
                eventData[sta.name] = edata

        fig_name = os.path.join(figdir, f'{self.otime.__unicode__()}_{self.latitude}_{self.longitude}_{self.depth}_{self.magnitude}')
        PlotEvent(eventData, fig_name, start, end, [theoy], [theop], [theos], 12)



    @classmethod
    def PlotMultiEvent(cls, eventl, start: UTCDateTime, end: UTCDateTime, olat: float, olon: float, stacls: dict, minf: float, maxf: float, amplifier: float, mpOnly = False):
        model = TauPyModel(model="PREM")
        eventData = {}
        figdir = os.path.join(cls.workdir, 'figures', 'event')
        
        if not os.path.isdir(figdir):
            os.makedirs(figdir)

        distd = {}
        for sta in stacls.values():
            result = _CalDist(sta.latitude, sta.longitude, olat, olon)
            distd[sta.name] = float(result['distancemeters']/1000)
        distd = {k: v for k, v in sorted(distd.items(), key=lambda x: x[1])}

        theoy = []
        theop = []
        theos = []
        for i in range(len(eventl)):
            theoy.append([])
            theop.append([])
            theos.append([])

        # for sta in stacls.values():
        for num, st in enumerate(distd.keys()):
            sta = stacls[st]
            dist = distd[st]
            edata = {}

            y = dist

            # dist = self.CalDist(sta.latitude, sta.longitude)
            data, delta = sta.GetData(start = start, end = end, minf = minf, maxf = maxf)
            if delta == 0:
                continue
            dpt, dst, mpt, mst = sta.GetPicks(start, end = end, delta = delta)
            if mpOnly and len(mpt) == 0 and len(mst) == 0:
                continue
            
            for i, t in enumerate(dpt):
                dpt[i] = t * delta
            for i, t in enumerate(dst):
                dst[i] = t * delta
            for i, t in enumerate(mpt):
                mpt[i] = t * delta
            for i, t in enumerate(mst):
                mst[i] = t * delta
            
            for i, e in enumerate(eventl):
                result = _CalDist(e[1], e[2], sta.latitude, sta.longitude)
                arrivals = model.get_travel_times(source_depth_in_km=e[3], distance_in_degree=float(result['distance']), phase_list=['P', 'p', 'S', 's'])
                p = 0
                s = 0
                theoy[i].append(y)
                for t in arrivals:
                    if (t.phase.name.lower() == 'p') and (p == 0):
                        theop[i].append(UTCDateTime(e[0]) + t.time - start)
                        p = 1
                    elif (t.phase.name.lower() == 's') and (s == 0):
                        theos[i].append(UTCDateTime(e[0]) + t.time - start)
                        s = 1

            edata['dpt'] = []
            edata['dst'] = []
            edata['mpt'] = mpt
            edata['mst'] = mst
            edata['pos'] = [y, amplifier]

            if data != None:
                edata['delta'] = delta
                for c, v in data.items():
                    if 'Z' in c:
                        edata['dataZ'] = v/max(v) * amplifier + y
                    elif '1' in c or 'E' in c:
                        edata['dataE'] = v/max(v) * amplifier + y
                    elif '2' in c or 'N' in c:
                        edata['dataN'] = v/max(v) * amplifier + y
                eventData[sta.name] = edata

        evt = []
        evy = []
        for i, e in enumerate(eventl):
            t = UTCDateTime(e[0]) - start
            result = _CalDist(e[1], e[2], olat, olon)
            d = float(result['distancemeters']/1000)
            evt.append(t)
            evy.append(d)
            theoy[i].append(d)
            theop[i].append(t)
            theos[i].append(t)

            theoy[i], theop[i], theos[i] = zip(*sorted(zip(theoy[i], theop[i], theos[i]), key=lambda x: x[0]))
        
        theoy = [list(x) for x in theoy]
        theop = [list(x) for x in theop]
        theos = [list(x) for x in theos]

        fig_name = os.path.join(figdir, f'{start.__unicode__()}_{end.__unicode__()}_{olat}_{olon}')
        PlotEvent(eventData, fig_name, 0, (end-start)/60, theoy, theop, theos, 20, evt, evy)