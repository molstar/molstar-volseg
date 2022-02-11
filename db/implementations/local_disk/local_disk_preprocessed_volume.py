import numpy

from db.interface.i_preprocessed_volume import IPreprocessedVolume


class LocalDiskPreprocessedVolume(IPreprocessedVolume):
    def __init__(self, down_sampled_data: numpy.ndarray):
        self.down_sampled_data = down_sampled_data

    def get_data(self) -> numpy.ndarray:
        return self.down_sampled_data
