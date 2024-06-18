from enum import Enum
from pathlib import Path
from typing import Any, Optional

from numcodecs import Blosc
from pydantic import BaseModel


class SegmentationPrimaryDescriptor(str, Enum):
    three_d_volume = "three_d_volume"
    mesh_list = "mesh_list"


class InputCase(str, Enum):
    map_only = "map_only"
    map_and_sff = "map_and_sff"
    omezarr = "omezarr"
    ometiff = "ometiff"


class InputKind(str, Enum):
    map = "map"
    sff = "sff"
    # ometiff = 'ometiff'
    omezarr = "omezarr"
    mask = "mask"
    # do we need to have it as separate types (am, mod, seg), or better to have general one and
    # leave it for a specific conversion function to check the extension and run conversion?
    application_specific_segmentation = "application_specific_segmentation"
    custom_annotations = "custom_annotations"
    nii_volume = "nii_volume"
    nii_segmentation = "nii_segmentation"
    geometric_segmentation = "geometric_segmentation"
    star_file_geometric_segmentation = "star_file_geometric_segmentation"
    ometiff_image = "ometiff_image"
    ometiff_segmentation = "ometiff_segmentation"
    # allencell_metadata_csv = 'extra_data'
    extra_data = "extra_data"
    tiff_image_stack_dir = "tiff_image_stack_dir"


class QuantizationDtype(str, Enum):
    u1 = "u1"
    u2 = "u2"


class Inputs(BaseModel):
    #    tuple[filename, kind]
    # kinds: 'map', 'sff', 'ome.tiff', 'ome-zarr', 'mask', 'am', 'mod', 'seg', 'custom_annotations' ?
    # depending on files list it runs preprocessing, if application specific - first converts to sff
    files: list[tuple[Path, InputKind]]


class VolumeParams(BaseModel):
    quantize_dtype_str: Optional[QuantizationDtype]
    # TODO: low priority: linear and log quantization
    quantize_downsampling_levels: Optional[tuple[int, ...]]
    force_volume_dtype: Optional[str]


class DownsamplingParams(BaseModel):
    max_size_per_downsampling_lvl_mb: Optional[float]
    min_size_per_downsampling_lvl_mb: Optional[float] = 5
    min_downsampling_level: Optional[int]
    max_downsampling_level: Optional[int]
    remove_original_resolution: Optional[bool] = False


class StoringParams(BaseModel):
    #  params_for_storing
    # 'auto'
    chunking_mode: str = "auto"
    # Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0)
    # TODO: figure out how to pass it
    compressor: object = Blosc(
        cname="lz4", clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0
    )
    # we use only 'zip'
    store_type: str = "zip"


class EntryData(BaseModel):
    # entry id (e.g. emd-1832) to be used as database folder name for that entry
    entry_id: str
    # source database name (e.g. emdb) to be used as DB folder name
    source_db: str
    #    actual source database ID of that entry (will be used to compute metadata)
    source_db_id: str
    #    actual source database name (will be used to compute metadata)
    source_db_name: str


class PreprocessorInput(BaseModel):
    inputs: Inputs
    volume: VolumeParams
    # optional - we may not need them (for OME Zarr there are already downsamplings)
    downsampling: Optional[DownsamplingParams]
    entry_data: EntryData
    # for intermediate data
    working_folder: Path

    # do we need these two here?
    # storing params perhaps should be here as temporary internal format (zarr) also uses them
    db_path: Path
    storing_params: StoringParams
    # add_segmentation_to_entry: bool = False
    # add_custom_annotations: bool = False
    custom_data: Optional[dict[str, Any]]


DEFAULT_PREPROCESSOR_INPUT = PreprocessorInput(
    inputs=Inputs(
        files=[
            (
                Path("test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map"),
                # Path('test-data/preprocessor/sample_volumes/new_emd-99999-200A.mrc'),
                # Path('test-data/preprocessor/sample_volumes/emd_9199.map'),
                # Path('test-data/preprocessor/sample_volumes/empiar/b3talongmusc20130301.mrc'),
                InputKind.map,
            ),
            (
                Path(
                    "test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff"
                ),
                # Path('test-data/preprocessor/sample_segmentations/emdb_sff/emd_1547.hff'),
                # Path('test-data/preprocessor/sample_segmentations/empiar/empiar_10070_b3talongmusc20130301.hff'),
                InputKind.sff,
            ),
        ]
    ),
    volume=VolumeParams(
        quantize_dtype_str=QuantizationDtype.u1, quantize_downsampling_levels=(1,)
    ),
    downsampling=DownsamplingParams(max_size_per_downsampling_lvl_mb=250),
    entry_data=EntryData(
        entry_id="emd-1832",
        source_db="emdb",
        source_db_id="emd-1832",
        source_db_name="emdb",
    ),
    working_folder=Path("preprocessor/temp/temp_zarr_hierarchy_storage"),
    storing_params=StoringParams(),
    db_path=Path("preprocessor/temp/test_db"),
)

OME_ZARR_PREPROCESSOR_INPUT = PreprocessorInput(
    inputs=Inputs(
        files=[
            (
                Path(
                    "temp/v2_temp_static_entry_files_dir/idr/idr-6001247/6001247.zarr"
                ),
                InputKind.omezarr,
            )
        ]
    ),
    volume=VolumeParams(
        quantize_dtype_str=QuantizationDtype.u1, quantize_downsampling_levels=(2,)
    ),
    downsampling=DownsamplingParams(max_size_per_downsampling_lvl_mb=250),
    entry_data=EntryData(
        entry_id="idr-6001247",
        source_db="idr",
        source_db_id="idr-6001247",
        source_db_name="idr",
    ),
    working_folder=Path("preprocessor/temp/temp_zarr_hierarchy_storage"),
    storing_params=StoringParams(),
    db_path=Path("preprocessor/temp/test_db"),
)
