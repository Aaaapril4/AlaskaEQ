import warnings
from pathlib import Path

import numpy as np
from loguru import logger
from mpi4py import MPI
from obspy import UTCDateTime, read_inventory
from obspy.clients.filesystem.tsindex import Client

warnings.filterwarnings("ignore")

comm = MPI.COMM_WORLD  # pylint: disable=c-extension-no-member
size = comm.Get_size()
rank = comm.Get_rank()

SEEDS = Path("/mnt/scratch/jieyaqi/alaska/data4phasenet")
XMLS = Path("/mnt/scratch/xiziyi/dataset/tongaml_continious_xml")
OUTPUTS = Path(
    "/mnt/scratch/xiziyi/dataset/tongaml_continious_response_removed")
client = Client("tongaml_continious_seeds.sqlite")


def remove_unused_list(process_list_this_rank_raw):
    # clean this rank
    filtered = []
    for index, net, sta, starttime, endtime in process_list_this_rank_raw:
        if len(client.get_availability(
                net, sta, "*", "*", starttime, endtime)) > 0:
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

    start = UTCDateTime("2009-06-01T00:00:00")
    index = 0
    for each in sorted(SEEDS.glob("*mseed")):
        sta, net, _ = each.name.split(".")
        for day in range(60):
            starttime = start+60*60*24*day*10
            endtime = start+60*60*24*(day*10+10)
            fname = OUTPUTS / \
                f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
            if not fname.exists():
                process_list.append((index, net, sta, starttime, endtime))
                index += 1

    process_list_this_rank_raw = np.array_split(process_list, size)[rank]
    process_list_this_rank, total = remove_unused_list(
        process_list_this_rank_raw)

    return process_list_this_rank, total


def process_kernel(index, net, sta, starttime, endtime, total):
    st = client.get_waveforms(
        net, sta, "*", "*", starttime-60*60, endtime+60*60)
    st_test = st.copy()
    st_test.merge(method=1)
    # check if mergable
    masks = []
    st_test.sort()
    for i in range(len(st_test)):
        if type(st_test[i].data) == np.ma.MaskedArray:
            masks.append(st_test[i].data.mask)
        else:
            masks.append(np.zeros(len(st_test[i].data), dtype=bool))
    # process
    st.merge(method=1, fill_value="latest")
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")

    inv = read_inventory(XMLS/f"IRISDMC-{sta}.{net}.xml")
    pre_filt = [0.01, 0.05, 20, 50]
    st.remove_response(output="VEL", pre_filt=pre_filt, zero_mean=False,
                       taper=False, inventory=inv)
    # mask to 0
    st.sort()
    for i in range(len(st)):
        st[i].data[masks[i]] = 0
    st.trim(starttime, endtime)
    st.interpolate(sampling_rate=40)

    if len(st) > 0:
        logger.info(
            f"[{rank}]: {index}/{total} {net}.{sta} {starttime}->{endtime}")
        fname = OUTPUTS / \
            f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
        st.write(str(fname), format='MSEED')


def process(process_list_this_rank, total):
    for index, net, sta, starttime, endtime in process_list_this_rank:
        process_kernel(index, net, sta, starttime, endtime, total)


if __name__ == "__main__":
    process_list_this_rank, total = get_process_list_this_rank()
    process(process_list_this_rank, total)
