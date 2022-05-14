from pathlib import Path
import zarr
import numpy as np
from preprocessor.src.preprocessors.i_data_preprocessor import IDataPreprocessor

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import GRID_METADATA_FILENAME, \
    ANNOTATION_METADATA_FILENAME
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler


def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root


class SFFPreprocessor(IDataPreprocessor):
    # TODO: import from e.g. axis methods etc.

    from ._hdf5_to_zarr import hdf5_to_zarr
    from ._volume_map_methods import read_volume_map_to_object, normalize_axis_order
    from ._process_X_data_methods import process_volume_data, process_segmentation_data
    from ._metadata_methods import temp_save_metadata, extract_annotation_metadata, extract_grid_metadata
    from ._volume_map_methods import read_and_normalize_map, read_volume_data

    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[1] / 'data/temp_zarr_hierarchy_storage'
        self.magic_kernel = MagicKernel3dDownsampler()
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path, volume_force_dtype=np.float32):
        '''
        Returns path to temporary zarr structure that will be stored permanently using db.store
        '''
        if segm_file_path is not None:
            self.temp_zarr_structure_path = self.hdf5_to_zarr(self.temp_root_path, segm_file_path)
        else:
            self.__init_empty_zarr_structure(volume_file_path)
        # Re-create zarr hierarchy
        zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
            self.temp_zarr_structure_path)

        # read map
        map_object = self.read_volume_map_to_object(volume_file_path)
        normalized_axis_map_object = self.normalize_axis_order(map_object)

        if segm_file_path is not None:
            self.process_segmentation_data(self.magic_kernel, zarr_structure)

        self.process_volume_data(zarr_structure, normalized_axis_map_object, volume_force_dtype)

        grid_metadata = self.extract_grid_metadata(zarr_structure, normalized_axis_map_object)
        self.temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, self.temp_zarr_structure_path)

        if segm_file_path is not None:
            annotation_metadata = self.extract_annotation_metadata(segm_file_path)
            self.temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, self.temp_zarr_structure_path)

        return self.temp_zarr_structure_path

    def __init_empty_zarr_structure(self, volume_file_path: Path):
        '''
        Creates EMPTY temp zarr structure for the case when just volume file is provided
        '''
        self.temp_zarr_structure_path = self.temp_root_path / volume_file_path.stem
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))
