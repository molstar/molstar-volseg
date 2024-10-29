from cellstar_preprocessor.tools.gunzip.gunzip import gunzip
from pydantic.dataclasses import dataclass
import os
from pathlib import Path
import resource
import shutil
import urllib.request
import zipfile

from cellstar_db.models import AssetKind, AssetInfo, AssetSourceInfo, CompressionFormat
from cellstar_preprocessor.tools.remove_path.remove_path import remove_path
import ome_zarr.utils


@dataclass
class Uncompressor:
    source: Path 
    compression_format: CompressionFormat
    # directory of file (if gz)
    destination: Path
    
    def uncompress(self):
        f = self.compression_format
        match f:
            case CompressionFormat.zip_dir:
                # TODO: will it work with normal non ometiff archieves
                # will it retrieve dir structure?
                with zipfile.ZipFile(str(self.source.resolve()), "r") as zip_ref:
                    for zip_info in zip_ref.infolist():
                        if zip_info.is_dir():
                            continue
                        zip_info.filename = os.path.basename(zip_info.filename)
                        zip_ref.extract(zip_info, str(self.destination.resolve()))
                return self.destination
            case CompressionFormat.gzipped_file | CompressionFormat.hff_gzipped_file | CompressionFormat.map_gzipped_file:
                # source wrong
                return gunzip(self.source, self.destination)
            # TODO: other
            case _:
                raise NotImplementedError(f'Support for format {f} has not been implemented yet')
    
    def remove_compressed(self):
        remove_path(self.source)