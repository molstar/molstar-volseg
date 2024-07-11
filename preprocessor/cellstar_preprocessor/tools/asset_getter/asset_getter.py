from dataclasses import dataclass
import os
from pathlib import Path
import resource
import shutil
import urllib.request
from uuid import uuid4
import zipfile

from cellstar_db.models import AssetKind, AssetInfo, AssetSourceInfo, CompressionFormat
from cellstar_preprocessor.tools.remove_path.remove_path import remove_path
from cellstar_preprocessor.tools.uncompresser.uncompresser import Uncompresser
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
            
        format = self.source_extension[1:]
        dest = self.destination
        dest_suffix = dest.suffix
        source_ext = self.source_extension
        if format not in CompressionFormat:
            assert dest_suffix == source_ext, \
                f'Destination file format {format}, dest_suffix {dest_suffix}, source_ext {source_ext} '
        else:
            dest.mkdir()
            assert dest.is_dir(), 'Destination for compressed file should be directory to uncompress to'
    
    @property
    def source_name(self):
        return self.asset_info.source.name
    
    @property
    def source_extension(self):
        return self.asset_info.source.extension
    
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
    def _uncompress(self, path: Path, destination_dir: Path):
        # uncompress
        # uncompressed_path = None
        unc = Uncompresser(source=path, compression_format=self.source_compression_format, destination_dir=destination_dir)
        unc.uncompress()
        unc.remove_compressed()
        kind = self.asset_kind
        if kind in [AssetKind.ometiff_image, AssetKind.ometiff_segmentation]:
            # TODO glob multiple resolutions
            # p: tuple[Path] = sorted()
            # (p.resolve() for p in Path(path).glob("**/*") if p.suffix in {".c", ".cc", ".cpp", ".hxx", ".h"})
            p: list[Path] = sorted(list(destination_dir.glob("*")))
            first_ometiff = p[0]
            return first_ometiff
        else:
            raise NotImplementedError(f"Support for {kind} was not implemented yet")
            
        # delete compressed
        # assert uncompressed_path is not None, 'Uncompressed path is None'
        # self.destination = uncompressed_path
        # return self.destination
    
    # def __download_to_dir(self):
        
    # def __download_to_file(self):
    #     pass 
    
    def _get_target_path(self):
        if self.source_compression_format is None:
            # download to file
            return self.destination
        else:
            # download to folder
            # print("Debug", self.source_compression_format.value)
            unique_archive_name = str(uuid4()) + '.' + str(self.source_compression_format.value)
            return self.destination / unique_archive_name
        
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
            case _:
                try:                
                    urllib.request.urlretrieve(uri, str(target_path.resolve()))
                    # return self.destination
                except Exception:
                    print(f"Failed to download, uri: {uri}")
            
        return self.destination
        
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
        kind =self.source_kind 
        dest = self.destination
        target_path = self._get_target_path()
        out = None
        match kind:
            case "external":
                self._download(target_path)            
            case "local":
                self._get_local(target_path)
            case _:
                raise ValueError(f'source_kind {kind} not supported')

        if self.source_compression_format is not None:
            assert dest.is_dir(), f"Destination {dest} should be directory" 
            # target_path = zip file in folder
            # will return path to first ometiff in theory
            # wrong target_path
            # 'preprocessor/cellstar_preprocessor/tests/test_data/inputs_for_tests/0eb3377b-afdd-4ec1-9125-9a93cb355aa5/tubhiswt-4D.zip/6ee65c60-ec2f-46d2-a9db-016d2a175f66.zip'
            target_path = self._uncompress(target_path, dest)
        # assert dest is None, f'Was unable to get {path}'
        
        # should return file always, not dir
        # NOTE: tiff stack later
        # wrong
        return target_path