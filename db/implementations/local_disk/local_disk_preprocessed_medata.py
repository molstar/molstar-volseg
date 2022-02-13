from typing import List
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class LocalDiskPreprocessedMetadata(IPreprocessedMetadata):
    def __init__(self, raw_zarr_metadata: object):
        self.raw_zarr_metadata = raw_zarr_metadata

    def lattice_ids(self) -> List[int]:
        return [0]  # self.raw_zarr_metadata.lattice_ids

    def down_samplings(self, lattice_id: int) -> List[int]:
        return [0]  # self.raw_zarr_metadata.down_samplings[lattice_id]
