from pathlib import Path
from generate_csv import generate_csv
from generate_yaml import generate_yaml
from index import per_index
from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD  # pylint: disable=c-extension-no-member
size = comm.Get_size()
rank = comm.Get_rank()

basedir = '/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2'
root = Path(basedir)
datad = root / "data"
nperdir = 130


def get_process_list_this_rank(process_list: list):
    '''
    assign a list to different rank
    '''
    comm.Barrier()
    if rank == 0:
        print(len(process_list), size)
        process_list_this_rank = np.array_split(process_list, size)
    else:
        process_list_this_rank = None
    
    process_list_this_rank = comm.scatter(process_list_this_rank, root = 0)
    print(f'rank[{rank}] receive {len(process_list_this_rank)} samples')

    return process_list_this_rank


def distribute_mseed_rank(mseed_this_rank: list, ndir: int, dirmap: dict):
    # split mseed into different dirs
    print(f'rank[{rank}] moving files')
    for idx, file in enumerate(mseed_this_rank):
        p = dirmap[idx % ndir + 1]
        file.rename(p / file.name)
    return


def process_dir_rank(dirnum_this_rank: list, dirmap: dict):
    '''
    index directory on different ranks
    '''
    for num in dirnum_this_rank:
        generate_csv(str(dirmap[num]), '/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', str(root / f'statime{num}.csv'), '2018-01-01T000000', '2022-12-31T235959')
        generate_yaml('scripts_phasenet/alaska.yaml', str(Path('/mnt/home/jieyaqi/code/PhaseNet-TF/configs/experiment') / f'alaska{num}.yaml'), num)
        per_index(str(dirmap[num]), str(root / f'data{num}.sqlite'))
    return


if __name__ == "__main__":
    if rank == 0:
        mseedl = list(datad.glob("*.mseed"))
        ndir = len(mseedl) // nperdir + bool(len(mseedl) % nperdir)
        dirmap = {}

        for i in range(1, ndir + 1):
            datap = root / f'data{i}'
            resultp = root / f'result{i}'
            datap.mkdir(parents=True, exist_ok=True)
            resultp.mkdir(parents=True, exist_ok=True)
            dirmap[i] = datap
    else:
        dirmap = None
        ndir = None
    
    comm.Barrier()
    dirmap = comm.bcast(dirmap, root = 0)
    ndir = comm.bcast(ndir, root = 0)

    dirnum_this_rank = get_process_list_this_rank(range(1, ndir + 1))
    process_dir_rank(dirnum_this_rank, dirmap)