# This code is to help remove instrumental response which can't find using xml file
import warnings
from pathlib import Path

import numpy as np
from loguru import logger
from obspy.clients.fdsn import Client as fdsn_client
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy import UTCDateTime, read_inventory
import multiprocessing as mp
import obspy

warnings.filterwarnings("ignore")

SEEDS = Path("/mnt/scratch/jieyaqi/alaska/test_190102_trimed")
XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")
OUTPUTS = Path(
    "/mnt/scratch/jieyaqi/alaska/phasenet/data_10day")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/timeseries.sqlite")
iris_client = fdsn_client("IRIS")


def get_process_list():
    # get all array
    # from 2009-06-01 to 2010-12-31
    process_list = []

    start = UTCDateTime("2019-01-01T00:00:00")
    index = 0
    staList = [".".join(f.name.split("/")[-1].split(".")[0:2]) for f in sorted(SEEDS.glob("*/*mseed"))]
    for each in set(staList):
        net, sta = each.split('.')
        for day in range(6):
            starttime = start+60*60*24*day*10
            endtime = start+60*60*24*(day*10+10)
            fname = OUTPUTS / \
                f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
            if not fname.exists():
                process_list.append((index, net, sta, starttime, endtime))
                index += 1

    return process_list


def process_kernel(index, net, sta, starttime, endtime):
    files = sorted(SEEDS.glob(f'{sta}/{net}.{sta}*.mseed'))
    
    st = obspy.Stream()
    for f in files:
        id, _,  start, end = f.name[:-6].split('_')
        if start <= UTCDateTime(end) and end >= UTCDateTime(start):
            sttemp = obspy.read(f)
            sttemp.trim(starttime, endtime)
            for tr in sttemp:
                st.append(tr)

    if len(st) == 0:
        logger.info(
                f"!Error accessing data: {net}.{sta} {starttime}->{endtime}")
        return
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")

    pre_filt = [0.01, 0.05, 20, 50]

    inv = read_inventory(XMLS/f"{net}.{sta}.xml")
    try:
        st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                    taper=False, inventory=inv)
    except ValueError:
        # logger.info(
        #             f"Cannot find instrumental response: {net}.{sta} {starttime}->{endtime}")
        # return
        inv = iris_client.get_stations(
                network = net,
                station = sta,
                channel = "HH?,BH?,EH?,SH?",
                starttime = starttime,
                endtime = endtime,
                level='response'
            )
        try:
            st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                        taper=False, inventory=inv)
        except ValueError:
            logger.info(
                        f"!Error finding instrumental response: {net}.{sta} {starttime}->{endtime}")
            return

    st.interpolate(sampling_rate=40)
    st.merge(method=1, fill_value="latest")

    if len(st) == 0:
        logger.info(
                f"!Error processing data: {net}.{sta} {starttime}->{endtime}")
        return
    
    # mask to 0
    masks = []
    st.sort()
    for i in range(len(st)):
        if type(st[i].data) == np.ma.MaskedArray:
            masks.append(st[i].data.mask)
        else:
            masks.append(np.zeros(len(st[i].data), dtype=bool))

    for i in range(len(st)):
        st[i].data[masks[i]] = 0
    
    st.trim(starttime, endtime)

    # padding other channels
    channels = []
    for tr in st:
        channels.append(tr.stats.channel[2])

    if 'Z' not in channels:
        trz = st[0].copy()
        trz.data = np.zeros(len(trz.data))
        trz.stats.channel = st[0].stats.channel[:2]+'Z'
        st.append(trz)

    if 'E' not in channels and '1' not in channels:
        tre = st[0].copy()
        tre.data = np.zeros(len(tre.data))
        tre.stats.channel = st[0].stats.channel[:2]+'E'
        st.append(tre)

    if 'N' not in channels and '2' not in channels:
        trn = st[0].copy()
        trn.data = np.zeros(len(trn.data))
        trn.stats.channel = st[0].stats.channel[:2]+'N'
        st.append(trn)

    if len(st) > 0:
        logger.info(
            f"Finished {index} {net}.{sta} {starttime}->{endtime}")
        fname = OUTPUTS / \
            f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
        st.write(str(fname), format='MSEED')



if __name__ == "__main__":
    process_list = get_process_list()
    with mp.Pool(10) as p:
        results = p.starmap(process_kernel, process_list)
