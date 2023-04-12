# To solve problem with obspy filesystem, no use anymore

import os
from obspy import UTCDateTime
from loguru import logger
import multiprocessing as mp
from pathlib import Path
import obspy
SEEDS = Path("/mnt/scratch/jieyaqi/alaska/waveform")
OUTPUTS = Path("/mnt/scratch/jieyaqi/alaska/waveform_trimed")

workdir = '/mnt/scratch/jieyaqi/alaska'

def trim_data(file):
    name = file.split('/')[-1]
    id, start, end = name.split('__')
    start = UTCDateTime(start)
    end = UTCDateTime(end.split('.')[0]) - 1
    
    stadir = OUTPUTS / id.split('.')[1]
    stadir.mkdir(parents=True, exist_ok=True)
    startstr = start.strftime('%Y%m%dT%H%M%SZ')
    endstr = end.strftime('%Y%m%dT%H%M%SZ')
    
    out = OUTPUTS / id.split('.')[1] / f'{id}__{startstr}__{endstr}.mseed'

    if out.exists():
        return

    try:
        st = obspy.read(file, format='mseed')
    except:
        return
    st.trim(start, end)

    logger.info(
                f"Trimmed [{os.getppid()}]: {id}__{start}__{end}.mseed")
    st.write(out, format = 'mseed')


if __name__ == '__main__':
    seedl = list(SEEDS.glob("*/*.mseed"))
    seedl = [str(x) for x in seedl]

    with mp.Pool(20) as p:
        p.map(trim_data, seedl)