from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class VolumeInfo:
    def __init__(self,
                 name: str,
                 metadata: IPreprocessedMetadata,
                 downsampling: int,
                 min_downsampled: float,
                 max_downsampled: float,
                 min_source: float,
                 max_source: float,
                 grid_size: list[int]):
        self.name = name
        self.metadata = metadata
        self.downsampling = downsampling
        self.min_downsampled = min_downsampled
        self.max_downsampled = max_downsampled
        self.min_source = min_source
        self.max_source = max_source
        self.grid_size = grid_size
