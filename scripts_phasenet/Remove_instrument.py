import warnings
from pathlib import Path
import calendar

import numpy as np
from loguru import logger
from mpi4py import MPI
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy.clients.fdsn import Client as fdsn_client
from obspy import UTCDateTime, read_inventory

warnings.filterwarnings("ignore")

comm = MPI.COMM_WORLD  # pylint: disable=c-extension-no-member
size = comm.Get_size()
rank = comm.Get_rank()

SEEDS = Path("/mnt/scratch/jieyaqi/alaska/test_190102_trimed")
XMLS = Path("/mnt/scratch/jieyaqi/alaska/station")
OUTPUTS = Path(
    "/mnt/scratch/jieyaqi/alaska/phasenet/data")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/timeseries.sqlite")
iris_client = fdsn_client("IRIS")

def remove_unused_list(process_list_this_rank_raw):
    # clean this rank
    filtered = []
    for index, net, sta, starttime, endtime in process_list_this_rank_raw:
        filtered.append((index, net, sta, starttime, endtime))
    # collect all filtered
    filtered = comm.gather(filtered, root=0)
    # scatter
    if rank == 0:
        filtered_all = []
        for each in filtered:
            filtered_all.extend(each)
        filtered_all.sort()
        # reset index
        f = []
        index = 0
        for _, net, sta, starttime, endtime in filtered_all:
            f.append((index, net, sta, starttime, endtime))
            index += 1
        filtered_all = f

        filtered_all_splitted = np.array_split(filtered_all, size)
        total = len(filtered_all)
    else:
        filtered_all_splitted = None
        total = None
    res_each_rank = comm.scatter(filtered_all_splitted, root=0)
    total = comm.bcast(total, root=0)

    return res_each_rank, total


def get_process_list_this_rank():
    # get all array
    # from 2009-06-01 to 2010-12-31
    process_list = []

    
    index = 0
    staList = [".".join(f.name.split("/")[-1].split(".")[0:2]) for f in sorted(SEEDS.glob("*/*mseed"))]
    for s in set(staList):
        net, sta = s.split('.')
        starttime = UTCDateTime("2019-01-01T00:00:00")
        for month in range(2):
            endtime = starttime+calendar.monthrange(starttime.year, starttime.month)[1] * 60 * 60 * 24 - 1
            fname = OUTPUTS / \
                f"{net}.{sta}.{starttime.year}-{starttime.month}.mseed"
            if not fname.exists():
                process_list.append((index, net, sta, starttime, endtime))
                index += 1
            starttime = endtime + 1

    process_list_this_rank_raw = np.array_split(process_list, size)[rank]
    process_list_this_rank, total = remove_unused_list(
        process_list_this_rank_raw)

    return process_list_this_rank, total


def process_kernel(index, net, sta, starttime, endtime, total):
    try:
        st = sq_client.get_waveforms(
            net, sta, "*", "*", starttime, endtime)
    except:
        logger.info(
                f"Cannot access data: {net}.{sta} {starttime}->{endtime}")
        return

    if len(st) == 0:
        logger.info(
                f"Cannot access data: {net}.{sta} {starttime}->{endtime}")
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")

    pre_filt = [0.01, 0.05, 20, 50]

    inv = read_inventory(XMLS/f"{net}.{sta}.xml")
    try:
        st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                    taper=False, inventory=inv)
    except ValueError:
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
                        f"Cannot find instrumental response: {net}.{sta} {starttime}->{endtime}")
            return

    st.interpolate(sampling_rate=40)
    st.merge(method=1, fill_value="latest")

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
            f"[{rank}]: {index}/{total} {net}.{sta} {starttime}->{endtime}")
        fname = OUTPUTS / \
            f"{net}.{sta}.{starttime.year}-{starttime.month}.mseed"
        st.write(str(fname), format='MSEED')


def process(process_list_this_rank, total):
    for index, net, sta, starttime, endtime in process_list_this_rank:
        process_kernel(index, net, sta, starttime, endtime, total)


if __name__ == "__main__":
    process_list_this_rank, total = get_process_list_this_rank()
    process(process_list_this_rank, total)
