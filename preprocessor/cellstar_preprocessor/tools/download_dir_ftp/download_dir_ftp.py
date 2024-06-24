import multiprocessing
from pathlib import Path
import ftplib, time
import urllib.request

HTTPS_BASE = 'https://ftp.ebi.ac.uk/empiar/world_availability/12017/data/Obese%20LacZ/ob_LacZ_2679_raw_8-bit/'

def _get_list_of_files_in_dir(ftp: ftplib.FTP, remotedir: str):
    ftp.cwd(remotedir)
    # TODO list of links
    
    return ftp.nlst()
    

def download_files(filenames: list[str], output_dir: Path):
    args = [(f"{HTTPS_BASE}{f}", (output_dir / f).resolve()) for f in filenames]
    print(args)
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        r = p.starmap(_urlretrieve_wrapper, args)
    
    
def _urlretrieve_wrapper(url: str, output: Path):
    try:
        urllib.request.urlretrieve(url, str(output.resolve()))
    except Exception as e:
        raise(e)


if __name__ == '__main__':    
    ftp = ftplib.FTP()
    HOST = "ftp.ebi.ac.uk"
    OUTPUT_DIR = Path('/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/obese_lacz_parallel')
    ftp.connect(HOST)
    ftp.login()
    t0 = time.time()
    
    # get list of files in subdir
    l = _get_list_of_files_in_dir(ftp, '/empiar/world_availability/12017/data/Obese LacZ/ob_LacZ_2679_raw_8-bit')
    download_files(l, OUTPUT_DIR)