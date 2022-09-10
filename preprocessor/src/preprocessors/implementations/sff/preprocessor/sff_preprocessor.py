import logging
from pathlib import Path
from typing import Union
import zarr
import numpy as np
from db.implementations.local_disk.local_disk_preprocessed_medata import LocalDiskPreprocessedMetadata
from preprocessor.src.preprocessors.i_data_preprocessor import IDataPreprocessor
from preprocessor.src.preprocessors.implementations.sff.preprocessor._zarr_methods import get_volume_downsampling_from_zarr, get_segmentation_downsampling_from_zarr
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import GRID_METADATA_FILENAME, \
    ANNOTATION_METADATA_FILENAME, MESH_SIMPLIFICATION_CURVE
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler
import mrcfile
import dask.array as da

def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root


class SFFPreprocessor(IDataPreprocessor):
    from ._hdf5_to_zarr import hdf5_to_zarr
    from ._volume_map_methods import normalize_axis_order_mrcfile
    from ._process_X_data_methods import process_volume_data, process_segmentation_data
    from ._metadata_methods import temp_save_metadata, extract_annotations, extract_metadata

    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[5] / 'data/temp_zarr_hierarchy_storage'
        self.magic_kernel = MagicKernel3dDownsampler()
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path, params_for_storing: dict, volume_force_dtype: Union[np.dtype, None]):
        '''
        Returns path to temporary zarr structure that will be stored permanently using db.store
        '''
        try:
            if segm_file_path is not None:
                self.temp_zarr_structure_path = SFFPreprocessor.hdf5_to_zarr(self.temp_root_path, segm_file_path)
            else:
                self.__init_empty_zarr_structure(volume_file_path)
            # Re-create zarr hierarchy
            zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
                self.temp_zarr_structure_path)

            # read map
            with mrcfile.mmap(str(volume_file_path.resolve())) as mrc_original:
                data: np.memmap = mrc_original.data
                if volume_force_dtype is not None:
                    data = data.astype(volume_force_dtype)
                else:
                    volume_force_dtype = data.dtype

                header = mrc_original.header

            if (volume_force_dtype in (np.uint8, np.int8)) or (
                    (volume_force_dtype in (np.uint16, np.int16)) and (params_for_storing['quantize_dtype_str'] in ['u2', '|u2', '>u2', '<u2'] )
                ):
                print(f'Quantization is skipped because input volume dtype is {volume_force_dtype} and requested quantization dtype is {params_for_storing["quantize_dtype_str"]}')
                del params_for_storing['quantize_dtype_str']

            dask_arr = da.from_array(data)
            # this one just swaps x to z as mrcfile writes it in specific order
            dask_arr = dask_arr.swapaxes(0, 2)
            # this should normalize
            dask_arr = SFFPreprocessor.normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)

            mesh_simplification_curve = MESH_SIMPLIFICATION_CURVE
            if segm_file_path is not None:
                SFFPreprocessor.process_segmentation_data(self.magic_kernel, zarr_structure, mesh_simplification_curve, params_for_storing=params_for_storing)

            SFFPreprocessor.process_volume_data(zarr_structure=zarr_structure, dask_arr=dask_arr, params_for_storing=params_for_storing, force_dtype=volume_force_dtype)

            grid_metadata = SFFPreprocessor.extract_metadata(
                zarr_structure,
                mrc_header=header,
                mesh_simplification_curve=mesh_simplification_curve,
                volume_force_dtype=volume_force_dtype)
            
            grid_dimensions: list = list(LocalDiskPreprocessedMetadata(grid_metadata).grid_dimensions())
            zarr_volume_arr_shape: list = list(get_volume_downsampling_from_zarr(1, zarr_structure).shape)
            
            if segm_file_path is not None and zarr_structure.primary_descriptor[0] == b'three_d_volume':
                zarr_segm_arr_shape: list = list(get_segmentation_downsampling_from_zarr(1, zarr_structure, 0).shape)
                assert grid_dimensions == zarr_segm_arr_shape, \
                f'grid dimensions from metadata {grid_dimensions} are not equal to segmentation arr shape {zarr_segm_arr_shape}'
            
            assert grid_dimensions == zarr_volume_arr_shape, \
                    f'grid dimensions from metadata {grid_dimensions} are not equal to volume arr shape {zarr_volume_arr_shape}'

            SFFPreprocessor.temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, self.temp_zarr_structure_path)

            if segm_file_path is not None:
                annotation_metadata = SFFPreprocessor.extract_annotations(segm_file_path)
                SFFPreprocessor.temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, self.temp_zarr_structure_path)
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return self.temp_zarr_structure_path

    def __init_empty_zarr_structure(self, volume_file_path: Path):
        '''
        Creates EMPTY temp zarr structure for the case when just volume file is provided
        '''
        self.temp_zarr_structure_path = self.temp_root_path / volume_file_path.stem
        try:
            assert self.temp_zarr_structure_path.exists() == False, \
                f'temp_zarr_structure_path: {self.temp_zarr_structure_path} already exists'
            store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e
