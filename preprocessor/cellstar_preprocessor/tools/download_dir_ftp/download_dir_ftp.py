from dataclasses import dataclass
import ftplib
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool    
import time
import urllib.request
from pathlib import Path

# HTTPS_BASE = "https://ftp.ebi.ac.uk/empiar/world_availability/12017/data/Obese%20LacZ/ob_LacZ_2679_raw_8-bit/"


def _download_file(ftp: ftplib.FTP, filename: str, destination_dir: Path):
    with open(destination_dir / filename, 'wb') as f:
        ftp.retrbinary('RETR ' + filename, f.write)


@dataclass
class FTPWrapper:
    ftp_host: str
    
    # with open(fullpath, 'wb') as f:
    #                 ftp.retrbinary('RETR ' + file[0], f.write)
    #             print(file[0] + '  downloaded')
    
    def __post_init__(self):
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.ftp_host)
        self.ftp.login()

    def _get_list_of_files_in_dir(self, directory: str):
        self.ftp.cwd(directory)
        return self.ftp.nlst()
    
    def download_dir(self, source_dir: str, destination_dir: Path):
        if not destination_dir.exists():
            destination_dir.mkdir()
        else:            
            assert destination_dir.is_dir(), 'Destination should be a directory if exists'
            
        filenames = self._get_list_of_files_in_dir(source_dir)
        # args = [(f"{HTTPS_BASE}{f}", (self.destination / f).resolve()) for f in filenames]
        # print(args)
        args = [(self.ftp, f, destination_dir) for f in filenames]
        # TODO: make it multiprocessing.Pool
        with ThreadPool(multiprocessing.cpu_count()) as p:
            p.starmap(_download_file, args)
        
    

# def download_dir_ftp(ftp_host: str):
#     ftp = ftplib.FTP()
#     # OUTPUT_DIR = Path(
#     #     "/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/obese_lacz_parallel"
#     # )
#     ftp.connect(ftp_host)
#     ftp.login()
#     # t0 = time.time()

#     # get list of files in subdir
#     l = _get_list_of_files_in_dir(
#         ftp, "/empiar/world_availability/12017/data/Obese LacZ/ob_LacZ_2679_raw_8-bit"
#     )
#     download_files(l, OUTPUT_DIR)



# def _get_list_of_files_in_dir(ftp: ftplib.FTP, remotedir: str):
#     ftp.cwd(remotedir)
#     # TODO list of links

#     return ftp.nlst()


# def download_files(filenames: list[str], output_dir: Path):
#     args = [(f"{HTTPS_BASE}{f}", (output_dir / f).resolve()) for f in filenames]
#     print(args)
#     with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
#         p.starmap(_urlretrieve_wrapper, args)


# def _urlretrieve_wrapper(url: str, output: Path):
#     try:
#         urllib.request.urlretrieve(url, str(output.resolve()))
#     except Exception as e:
#         raise (e)


# if __name__ == "__main__":
    # SOURCE_DIR = '/empiar/world_availability/12017/data/Obese LacZ/ob_LacZ_2679_raw_8-bit'
    # DESTINATION_DIR = Path('preprocessor/cellstar_preprocessor/tools/download_dir_ftp/test_dir')
    # w = FTPWrapper(
    #     ftp_host="ftp.ebi.ac.uk",
    #     # destination=Path('preprocessor/cellstar_preprocessor/tools/download_dir_ftp/test_dir')
    # )
    # w.download_dir(SOURCE_DIR, DESTINATION_DIR)