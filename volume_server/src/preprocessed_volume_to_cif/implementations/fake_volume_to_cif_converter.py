from typing import Union

from db.interface.i_preprocessed_db import ProcessedVolumeSliceData
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.src.preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter


class FakeVolumeToCifConverter(IVolumeToCifConverter):
    def convert_meshes(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata,
                       downsampling: int,
                       grid_size: list[int]) -> Union[bytes, str]:
        pass

    def convert_metadata(self, metadata: IPreprocessedMetadata):
        return metadata

    def __init__(self):
        pass

    def convert(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, downsampling: int,
                grid_size: list[int]) -> Union[bytes, str]:
        pass
