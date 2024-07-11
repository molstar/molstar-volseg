from dataclasses import dataclass
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
class Uncompresser:
    source: Path 
    compression_format: CompressionFormat
    destination_dir: Path
    
    def uncompress(self):
        f = self.compression_format
        match f:
            case CompressionFormat.zip_archive:
                # TODO: will it work with normal non ometiff archieves
                # will it retrieve dir structure?
                with zipfile.ZipFile(str(self.source.resolve()), "r") as zip_ref:
                    for zip_info in zip_ref.infolist():
                        if zip_info.is_dir():
                            continue
                        zip_info.filename = os.path.basename(zip_info.filename)
                        zip_ref.extract(zip_info, str(self.destination_dir.resolve()))

            # case CompressionFormat.gzip_archive:
            #     pass
            # TODO: other
            case _:
                raise NotImplementedError(f'Support for format {f} has not been implemented yet')
    
    def remove_compressed(self):
        remove_path(self.source)