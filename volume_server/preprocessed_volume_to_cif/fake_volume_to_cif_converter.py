import numpy as np

from .i_volume_to_cif_converter import IVolumeToCifConverter


class FakeVolumeToCifConverter(IVolumeToCifConverter):
    def __init__(self):
        pass

    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        return preprocessed_volume
