from pathlib import Path
from huggingface_hub import HfApi
import zipfile

api = HfApi()
zip_num = 2000

def _remove_uploaded(log: Path, filelist: list) -> list:
    '''
    remove uploaded files from filelist
    '''
    with log.open() as f:
        uploaded_list = f.readlines()
    for line in uploaded_list:
        file = Path(line.strip())
        for k, v in filelist.items():
            if file in v:
                v.remove(file)
    for k, v in filelist.copy().items():
        if len(v) == 0:
            del filelist[k]
    return filelist


def _write_uploaded(log: Path, uploaded) -> None:
    '''
    write uploaded file to log
    '''
    with log.open("a") as f:
        f.write(str(uploaded) + '\n')
    return


def _is_filtered(file: Path, filter: list[str]) -> bool:
    '''
    check if the file path need to be filtered
    '''
    for pattern in filter:
        if pattern in str(file):
            return True
    return False


def _walk_dir(datap: Path, filter: list[str]) -> dict[list[Path]]:
    '''
    walk through the directory
    '''
    filelist = {}

    for file in datap.glob('*'):
        if _is_filtered(file, filter):
            continue

        if file.is_dir():
            for k, v in _walk_dir(file, filter).items():
                if k not in filelist:
                    filelist[k] = v
                else:
                    filelist[k] += v
        else:
            parent = str(file.parent)
            if parent not in filelist:
                filelist[parent] = []
            filelist[parent].append(file)

    return filelist


def _loadfiles(datap: Path, filter: list[str], log: Path) -> list[Path]:
    '''
    load all the files to upload
    '''
    filelist = _walk_dir(datap, filter)
    filelist = _remove_uploaded(log, filelist)
    return filelist


def _upload_single_file(file_path: str, path_in_repo: str) -> None:
    api.upload_file(
        path_or_fileobj=file_path,
        path_in_repo=path_in_repo,
        repo_id='Aaaapril/PS_Alaska',
        repo_type='dataset',
    )
    return


def _upload_file(filelist: list[Path], log: Path, datap: Path, rootp: Path) -> None:
    for file in filelist:
        _upload_single_file(str(file), str(file.relative_to(rootp)))
        _write_uploaded(log, file)
    return


def _zip_folder(filelist: list[Path], zip_name: str, zip_log: Path) -> list[Path]:
    if not zip_log.exists():
        zip_log.touch()
    _write_uploaded(zip_log, f'{str(filelist[0].parent)}:{zip_name.split("/")[-1][:-4]}')
    with zipfile.ZipFile(zip_name, 'w') as f:
        i = 0
        while i < zip_num and i < len(filelist):
            f.write(str(filelist[i]), arcname=filelist[i].name)
            _write_uploaded(zip_log, filelist[i])
            i += 1
    if len(filelist) > zip_num:
        return filelist[zip_num:]
    else:
        return []


def _upload_zip(datap: Path, rootp: Path, zip_log: Path, log: Path) -> None:
    with zip_log.open() as f:
        parent, zip_name = f.readline().strip().split(':')
    
    _upload_single_file(str(datap / f'{zip_name}.zip'), str((Path(parent) / f'{zip_name}.zip').relative_to(rootp)))

    with zip_log.open() as f:
        lines = f.read()
    with log.open('a') as f:
        f.write(lines)
        f.write(f'{parent}:{zip_name}\n')
    
    zip_log.unlink()
    (datap/f'{zip_name}.zip').unlink()
    return


def _upload_folder(log: Path, datap: Path, rootp: Path, **kwargs) -> None:
    zip_log = datap / "zip_log"

    if 'filelist' in kwargs:
        with log.open() as f:
            lines = f.readlines()
        if lines[-1].strip().split(':')[0] == str(kwargs['parent']):
            current_num, _, total_num = lines[-1].strip().split(':')[1].split('-')
            current_num = int(current_num) + 1
            total_num = int(total_num)
        else:
            total_num = len(kwargs['filelist']) // zip_num + bool(len(kwargs['filelist']) % zip_num)
            current_num = 0
        while len(kwargs['filelist']) != 0:
            zip_name = f'{current_num:05d}-of-{total_num:05d}'
            kwargs['filelist'] = _zip_folder(kwargs['filelist'], str(datap / f'{zip_name}.zip'), zip_log)
            _upload_zip(datap, rootp, zip_log, log)
            current_num += 1

    else:
        _upload_zip(datap, rootp, zip_log, log)
    

    return


def upload_dataset(dataset_dir: str, root_dir: str) -> None:
    '''
    main function to upload dataset
    '''
    datap = Path(dataset_dir)
    rootp = Path(root_dir)
    log = datap / 'uploaded'
    if not log.exists():
        log.touch()
    
    if (datap / 'zip_log').exists():
        _upload_folder(log, datap, root_dir)

    filelist = _loadfiles(datap, ['.git', 'PNTFIter1', 'uploaded', 'chunk'], log)

    for k, v in filelist.items():
        if len(v) < 10:
            _upload_file(v, log, datap, rootp)
        else:
            _upload_folder(log, datap, rootp, filelist = v, parent = k)
        
    return


# Upload dataset to huggingface
upload_dataset('/mnt/scratch/jieyaqi/alaska/final/PS_Alaska/ManualPick_ai4eps', '/mnt/scratch/jieyaqi/alaska/final/PS_Alaska')

