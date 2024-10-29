from cellstar_preprocessor.tools.download_dir_ftp.download_dir_ftp import FTPWrapper
from pydantic.dataclasses import dataclass
import os
from pathlib import Path
import resource
import shutil
import urllib.request
from uuid import uuid4
import zipfile
from urllib.parse import urlparse

from cellstar_db.models import AssetKind, AssetInfo, AssetSourceInfo, CompressionFormat
from cellstar_preprocessor.tools.remove_path.remove_path import remove_path
from cellstar_preprocessor.tools.uncompresser.uncompresser import Uncompressor
import ome_zarr.utils


@dataclass
class AssetGetter:
    asset_info: AssetInfo
    destination: Path
    
    def __post_init__(self):
        
        
        if self.destination.exists():
            remove_path(self.destination)
        
        if not self.destination.parent.exists():
            self.destination.parent.mkdir(parents=True)
        
        
        # 1. Destination format = list of suffixes
        # 2. Need to be equal to the same list from asset
        
        
        source_extensions = self.asset_info.extensions 
        destination = self.destination
        
        assert self.destination_extension in source_extensions, \
            f'Source and destination should have compatible extensions'
            # f'Destination file format {format}, dest_suffix {dest_suffixes}, source_ext {source_ext} '
        
        # check if need to create dir
        # in other way
        if self.source_compression_format in {CompressionFormat.zip_dir, CompressionFormat.tar_gz_dir}:
            destination.mkdir()
            assert destination.is_dir(), 'Destination for compressed dir should be directory to uncompress to'
    
    @property
    def source_name(self):
        return self.asset_info.source.name
    
    @property
    def source_format(self):
        l = [i for i in self.asset_info.source.extensions]
        s = "".join(l)[1:]
        return s
    
    @property
    def asset_kind(self) -> AssetKind:
        return self.asset_info.kind
    
    @property
    def source_kind(self):
        return self.asset_info.source.kind
    
    @property
    def soure_uri(self):
        return self.asset_info.source.uri
    
    @property
    def destination_extension(self):
        return "".join(self.destination.suffixes)
    
    @property
    def source_compression_format(self):
        return self.asset_info.source.compression
    
    # def _unzip_multiseries_ometiff_zip(self):

    
    # TODO: use case 1
    # regular file: user provides destination as abc.mrc
    # we download/copy to it
    # use case 2:
    # zip 
    # user provides destination as mnt/temp/ometiff_tubsht/
    # FOLDER
    # we first download to that folder, not as folder
    # then uncompress
    # 
    def _uncompress(self, path: Path, destination: Path):
        # uncompress
        # uncompressed_path = None
        unc = Uncompressor(source=path, compression_format=self.source_compression_format, destination=destination)
        uncompressed = unc.uncompress()
        unc.remove_compressed()
        kind = self.asset_kind
        if kind in [AssetKind.ometiff_image, AssetKind.ometiff_segmentation]:
            assert destination.is_dir(), f"Destination {destination} should be directory"
            # TODO glob multiple resolutions
            # p: tuple[Path] = sorted()
            # (p.resolve() for p in Path(path).glob("**/*") if p.suffix in {".c", ".cc", ".cpp", ".hxx", ".h"})
            p: list[Path] = sorted(list(destination.glob("*")))
            first_ometiff = p[0]
            return first_ometiff
        else:
            return uncompressed
            # return 
            # raise NotImplementedError(f"Support for {kind} was not implemented yet")
            
            
        # delete compressed
        # assert uncompressed_path is not None, 'Uncompressed path is None'
        # self.destination = uncompressed_path
        # return self.destination
    
    # def __download_to_dir(self):
        
    # def __download_to_file(self):
    #     pass 
    
    def _get_target_path(self):
        if self.source_compression_format:
            if self.source_compression_format not in {CompressionFormat.zip_dir, CompressionFormat.tar_gz_dir}:
            # download to file
            # TODO: fix
            # should return with all suffixes as in source
                return self.source_name
            else:
            # download to folder
            # resolve separately
            # print("Debug", self.source_compression_format.value)
                unique_archive_name = str(uuid4()) + '.' + str(self.source_compression_format.value)
                return self.destination / unique_archive_name
        else:
            return self.destination
        
    def _download(self, target_path: Path):
        # add here something to handle downloading zip TO self.destination
        # similar to omezarr
        # download to folder?
        asset_kind = self.asset_kind
        uri = self.soure_uri
        match asset_kind:
            case AssetKind.omezarr:
                # NOTE: downloads TO dir, i.e. create XXXX.zar in provided path
                # We need to create one level up
                # 1. Download in parent of output_path
                ome_zarr.utils.download(uri, str(self.destination.parent.resolve()))
                # 2. rename to whatever is provided
                downloaded_path = Path(self.destination.parent / self.source_name)
                downloaded_path.rename(self.destination.resolve())
                # return self.destination
            case AssetKind.tiff_image_stack_dir | AssetKind.tiff_segmentation_stack_dir:
                # from ftp
                # uri - path to folder
                parsed_url = urlparse(uri)
                ftp_host = parsed_url.hostname
                w = FTPWrapper(ftp_host)
                print(parsed_url.path)
                w.download_dir(parsed_url.path, self.destination)
            case _:
                try:                
                    # wrong target path
                    # and parent does not exist
                    urllib.request.urlretrieve(uri, target_path)
                    # return self.destination
                except Exception:
                    print(f"Failed to download, uri: {uri}")
            
        return target_path
        
    def _get_local(self, target_path: Path):
        uri = self.soure_uri
        match self.asset_kind:
            # TODO: other?
            case AssetKind.omezarr:
                shutil.copytree(uri, target_path)
            case _:
                # first get then uncompress     
                shutil.copy2(uri, target_path)
                
        return self.destination
                
    def get_asset(self):
        kind = self.source_kind 
        dest = self.destination
        target_path = self._get_target_path()
        # target path should be with gz and all extensions
        # basically same to source uri last component 
        match kind:
            case "external":
                self._download(target_path)            
            case "local":
                self._get_local(target_path)
            case _:
                raise ValueError(f'source_kind {kind} not supported')

        if self.source_compression_format is not None:
            # dest should be without gz suffix
            target_path = self._uncompress(target_path, dest)
        
        return target_path