import numpy as np

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter


class FakeVolumeToCifConverter(IVolumeToCifConverter):
    def convert_metadata(self, metadata: IPreprocessedMetadata):
        return metadata

    def __init__(self):
        pass

    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        return preprocessed_volume
