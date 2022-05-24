import numpy as np

from preprocessor.src.preprocessors.implementations.sff.segmentation_set_table import SegmentationSetTable


class DownsamplingLevelDict:
    def __init__(self, level_dict):
        '''
        Dict for categorical set downsampling level
        '''
        self.downsampling_ratio: int = level_dict['ratio']
        self.grid: np.ndarray = level_dict['grid']
        self.set_table: SegmentationSetTable = level_dict['set_table']

    def get_grid(self):
        return self.grid
    
    def get_set_table(self):
        return self.set_table

    def get_ratio(self):
        return self.downsampling_ratio