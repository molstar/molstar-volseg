import abc
from typing import Union

from db.interface.i_preprocessed_db import ProcessedVolumeSliceData
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata

from volume_server.src.requests.request_box import RequestBox

class IVolumeToCifConverter(abc.ABC):
    @abc.abstractmethod
    def convert_meshes(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, downsampling: int,
                grid_size: list[int]) -> Union[bytes, str]:
        pass

    @abc.abstractmethod
    def convert(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, box: RequestBox) -> Union[bytes, str]:
        pass

    @abc.abstractmethod
    def convert_metadata(self, metadata: IPreprocessedMetadata):
        pass
