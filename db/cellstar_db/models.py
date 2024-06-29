from enum import Enum
from pathlib import Path
from typing import Any, List, Literal, Optional, Protocol, TypedDict, Union

from numcodecs import Blosc
import numpy as np
import zarr
from pydantic import BaseModel, Field

class PreprocessorMode(str, Enum):
    add = "add"
    extend = "extend"


class EntryMetadata(BaseModel):
    description: str | None
    url: str | None


class QuantizationDtype(str, Enum):
    u1 = "u1"
    u2 = "u2"


class PreprocessorParameters(BaseModel):
    '''
    Preprocessor parameters for the purpose of
    building database. No working folder, db_path
    '''
    quantize_dtype_str: QuantizationDtype | None
    quantize_downsampling_levels: list[int] | None
    force_volume_dtype: str | None
    max_size_per_downsampling_lvl_mb: float | None
    min_size_per_downsampling_lvl_mb: float | None
    min_downsampling_level: int | None
    max_downsampling_level: int | None
    remove_original_resolution: bool | None


class SegmentationKind(str, Enum):
    lattice = "lattice"
    mesh = "mesh"
    primitve = "primitive"

class InputKind(str, Enum):
    map = "map"
    sff = "sff"
    omezarr = "omezarr"
    mask = "mask"
    application_specific_segmentation = "application_specific_segmentation"
    custom_annotations = "custom_annotations"
    nii_volume = "nii_volume"
    nii_segmentation = "nii_segmentation"
    geometric_segmentation = "geometric_segmentation"
    ometiff_image = "ometiff_image"
    ometiff_segmentation = "ometiff_segmentation"
    extra_data = "extra_data"

class RawInput(BaseModel):
    path: str | Path
    kind: InputKind

class PreprocessorArguments(PreprocessorParameters):
    '''
    Full list of preprocessor arguments
    '''
    mode: PreprocessorMode
    entry_id: str
    source_db: str
    source_db_id: str
    source_db_name: str
    working_folder: str
    db_path: str
    inputs: list[RawInput]
  
class RawInputFileResourceInfo(BaseModel):
    kind: Literal["local", "external"]
    uri: str


class RawInputFileInfo(BaseModel):
    kind: InputKind
    resource: RawInputFileResourceInfo
    preprocessor_parameters: PreprocessorParameters | None


class RawInputFilesDownloadParams(BaseModel):
    entry_id: str
    source_db: str
    source_db_id: str
    source_db_name: str
    inputs: list[RawInputFileInfo]


# JSON - list of InputForBuildingDatabase
# TODO: can be a JSON schema instead
# NOTE: Single entry input
# TODO: infer schema from json
# TODO: use this class when parsing
# need to create preprocessor input from


class InputForBuildingDatabase(BaseModel):
    quantize_dtype_str: QuantizationDtype | None
    quantize_downsampling_levels: list[int] | None
    force_volume_dtype: str | None
    max_size_per_downsampling_lvl_mb: float | None
    min_size_per_downsampling_lvl_mb: float | None
    min_downsampling_level: int | None
    max_downsampling_level: int | None
    remove_original_resolution: bool | None
    entry_id: str
    source_db: str
    source_db_id: str
    source_db_name: str
    # working_folder: str
    # db_path: str
    inputs: list[RawInput]


class OMETIFFSpecificExtraData(BaseModel):
    # missing_dimension: str
    cell_stage: Optional[str]
    ometiff_source_metadata: Optional[dict]


class VolumeExtraData(BaseModel):
    voxel_size: list[float, float, float] | None
    # map sequential channel ID (e.g. "1" as string)
    # to biologically meaningfull channel id (string)
    channel_ids_mapping: dict[str, str] | None
    dataset_specific_data: object | None


class SegmentationExtraData(BaseModel):
    voxel_size: list[float, float, float] | None
    # map segmentation number (dimension) in case of >3D array (e.g. OMETIFF)
    # or in case segmentation ids are given as numbers by default
    # to segmentation id (string)
    segmentation_ids_mapping: dict[str, str] | None
    # lattice_id (artificial, keys from segmentation_ids_mapping)
    # to dict with keys = segment ids and values = segment names?
    # could work, easier than modify descriptions via preprocessor command
    # CURRENTLY IS A KEY THAT IS PROVIDED IN SEGMENTATION_IDS_MAPPING
    segment_ids_to_segment_names_mapping: dict[str, dict[str, str]] | None
    # could have key = "ometiff"
    dataset_specific_data: object | None


class ExtraData(BaseModel):
    entry_metadata: Optional[EntryMetadata]
    volume: Optional[VolumeExtraData]
    segmentation: Optional[SegmentationExtraData]
    # for custom things
    # metadata: Optional[object]
    # dataset_specific_data: Optional[object]


# METADATA DATA MODEL


class SamplingBox(BaseModel):
    origin: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    grid_dimensions: list[int, int, int]


class TimeTransformation(BaseModel):
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, Literal["all"]]
    factor: float


class DownsamplingLevelInfo(BaseModel):
    level: int
    available: bool


class SamplingInfo(BaseModel):
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[DownsamplingLevelInfo]
    # the only thing which changes with SPATIAL downsampling is box!
    boxes: dict[int, SamplingBox]
    time_transformations: Optional[list[TimeTransformation]]
    source_axes_units: dict[str, str]
    # e.g. (0, 1, 2) as standard
    original_axis_order: list[int, int, int]


class TimeInfo(BaseModel):
    kind: str
    start: int
    end: int
    units: str


class SegmentationLatticesMetadata(BaseModel):
    # e.g. label groups (Cell, Chromosomes)
    segmentation_ids: list[str]
    segmentation_sampling_info: dict[str, SamplingInfo]
    time_info: dict[str, TimeInfo]


class GeometricSegmentationSetsMetadata(BaseModel):
    segmentation_ids: list[str]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]


class MeshMetadata(BaseModel):
    num_vertices: int
    num_triangles: int
    num_normals: Optional[int]


class MeshListMetadata(BaseModel):
    mesh_ids: dict[int, MeshMetadata]


class DetailLvlsMetadata(BaseModel):
    detail_lvls: dict[int, MeshListMetadata]


class MeshComponentNumbers(BaseModel):
    segment_ids: dict[int, DetailLvlsMetadata]


class MeshesMetadata(BaseModel):
    # maps timeframe index to MeshComponentNumbers
    mesh_timeframes: dict[int, MeshComponentNumbers]
    detail_lvl_to_fraction: dict


class MeshSegmentationSetsMetadata(BaseModel):
    segmentation_ids: list[str]
    # maps segmentation_id to MeshesMetadata
    segmentation_metadata: dict[str, MeshesMetadata]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]


class VolumeDescriptiveStatistics(BaseModel):
    mean: float
    min: float
    max: float
    std: float


class VolumeSamplingInfo(SamplingInfo):
    # resolution -> time -> channel_id
    descriptive_statistics: dict[int, dict[int, dict[str, VolumeDescriptiveStatistics]]]


class VolumesMetadata(BaseModel):
    channel_ids: list[str]
    # Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo


class EntryId(BaseModel):
    source_db_name: str
    source_db_id: str


class Metadata(BaseModel):
    entry_id: EntryId
    volumes: VolumesMetadata | None
    segmentation_lattices: Optional[SegmentationLatticesMetadata]
    segmentation_meshes: Optional[MeshSegmentationSetsMetadata]
    geometric_segmentation: Optional[GeometricSegmentationSetsMetadata]
    entry_metadata: EntryMetadata | None


# END METADATA DATA MODEL

# ANNOTATIONS DATA MODEL


class VolumeChannelAnnotation(BaseModel):
    # uuid
    channel_id: str
    # with transparency
    color: tuple[float, float, float, float]
    label: Optional[str]


class SegmentAnnotationData(BaseModel):
    # label-value in NGFF
    # uuid
    id: Optional[str]
    segment_kind: SegmentationKind
    segment_id: int
    segmentation_id: str
    color: Optional[list[float, float, float, float]]
    time: Optional[int | list[int | tuple[int, int]]]
    # other props added later if needed


class ExternalReference(BaseModel):
    # uuid
    id: Optional[str]
    resource: Optional[str]
    accession: Optional[str]
    label: Optional[str]
    description: Optional[str]
    url: Optional[str]


class TargetId(BaseModel):
    segmentation_id: str
    segment_id: int


class DetailsText(BaseModel):
    format: Literal["text", "markdown"]
    text: str


class DescriptionData(BaseModel):
    # uuid
    id: Optional[str]
    target_kind: SegmentationKind | Literal["entry"]
    target_id: Optional[TargetId]
    name: Optional[str]
    external_references: Optional[list[ExternalReference]]
    is_hidden: Optional[bool]
    time: Optional[int | list[int | tuple[int, int]]]

    details: Optional[DetailsText]
    metadata: Union[dict[str, Any], None]


class AnnotationsMetadata(BaseModel):
    name: Optional[str]
    entry_id: EntryId
    # id => DescriptionData
    descriptions: dict[str, DescriptionData]
    # NOTE: on frontend, segment key = `${kind}:{segmentation_id}:{segment_id}`
    segment_annotations: list[SegmentAnnotationData]
    # Only in SFF
    details: Optional[str]
    volume_channels_annotations: Optional[list[VolumeChannelAnnotation]]


# END ANNOTATIONS DATA MODEL


# "DATA" DATA MODEL


class LatticeSegmentationData(TypedDict):
    grid: zarr.Array
    # NOTE: single item in the array which is a Dict
    set_table: zarr.Array


class SingleMeshZattrs(TypedDict):
    num_vertices: int
    area: float
    # TODO: add these two
    num_triangles: int
    num_normals: int


class SingleMeshSegmentationData(TypedDict):
    mesh_id: str
    vertices: zarr.Array
    triangles: zarr.Array
    normals: zarr.Array
    attrs: SingleMeshZattrs


class ShapePrimitiveKind(str, Enum):
    sphere = "sphere"
    tube = "tube"
    cylinder = "cylinder"
    box = "box"
    ellipsoid = "ellipsoid"
    pyramid = "pyramid"


class ShapePrimitiveBase(BaseModel):
    # NOTE: to be able to refer to it in annotations
    id: int
    kind: ShapePrimitiveKind
    # NOTE: color in annotations


class RotationParameters(BaseModel):
    axis: tuple[float, float, float]
    radians: float


class Sphere(ShapePrimitiveBase):
    # in angstroms
    center: tuple[float, float, float]
    radius: float


class Box(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: RotationParameters


class Cylinder(ShapePrimitiveBase):
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    radius_bottom: float
    radius_top: float  # =0 <=> cone


class Ellipsoid(ShapePrimitiveBase):
    dir_major: tuple[float, float, float]
    dir_minor: tuple[float, float, float]
    center: tuple[float, float, float]
    radius_scale: tuple[float, float, float]


class Pyramid(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: RotationParameters


class ShapePrimitiveData(BaseModel):
    shape_primitive_list: list[ShapePrimitiveBase]


class GeometricSegmentationData(BaseModel):
    segmentation_id: str
    # maps timeframe index to ShapePrimitivesData
    primitives: dict[int, ShapePrimitiveData]


class ZarrRoot(TypedDict):
    # resolution => timeframe index => channel
    volume_data: list[dict[int, list[dict[int, list[dict[int, zarr.Array]]]]]]
    # segmentation_id => downsampling => timeframe index
    lattice_segmentation_data: list[
        dict[str, list[dict[int, list[dict[int, LatticeSegmentationData]]]]]
    ]
    # segmentation_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist
    mesh_segmentation_data: list[
        str,
        dict[
            int,
            list[
                dict[int, list[dict[int, list[dict[int, SingleMeshSegmentationData]]]]]
            ],
        ],
    ]


# Files:
# NOTE: saved as JSON/Msgpack directly, without temporary storing in .zattrs
GeometricSegmentationJson = list[GeometricSegmentationData]

# END "DATA" DATA MODEL


# SERVER OUTPUT DATA MODEL (MESHES, SEGMENTATION LATTICES, VOLUMES)


class MeshData(BaseModel):
    mesh_id: int
    vertices: np.ndarray = Field(default_factory=lambda: np.zeros(10))  # shape = (n_vertices, 3)
    triangles: np.ndarray = Field(default_factory=lambda: np.zeros(10))  # shape = (n_triangles, 3)
    normals: Optional[np.ndarray] = Field(default_factory=lambda: np.zeros(10))
    
    class Config:
        arbitrary_types_allowed = True

MeshesData = list[MeshData]


class LatticeSegmentationSliceData(BaseModel):
    # array with set ids
    category_set_ids: np.ndarray = Field(default_factory=lambda: np.zeros(10))
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: dict
    lattice_id: int
    
    class Config:
        arbitrary_types_allowed = True


class SliceData(BaseModel):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[LatticeSegmentationSliceData]
    volume_slice: Optional[np.ndarray] = Field(default_factory=lambda: np.zeros(10))
    channel_id: Optional[str]
    time: int

    class Config:
        arbitrary_types_allowed = True

# END SERVER OUTPUT DATA MODEL

# INPUT DATA MODEL


class ShapePrimitiveInputParams(BaseModel):
    id: int
    color: list[float, float, float, float]


class RotationInputParameters(BaseModel):
    axis: tuple[float, float, float]
    radians: float


class SphereInputParams(ShapePrimitiveInputParams):
    center: tuple[float, float, float]
    radius: float


class BoxInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: RotationInputParameters


class CylinderInputParams(ShapePrimitiveInputParams):
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    radius_bottom: float
    radius_top: float  # =0 <=> cone


class EllipsoidInputParams(ShapePrimitiveInputParams):
    dir_major: tuple[float, float, float]
    dir_minor: tuple[float, float, float]
    center: tuple[float, float, float]
    radius_scale: tuple[float, float, float]


class PyramidInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: tuple[float, float, float]
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: tuple[float, float, float]
    rotation: RotationInputParameters


class ShapePrimitiveInputData(BaseModel):
    kind: ShapePrimitiveKind
    parameters: Union[
        SphereInputParams,
        PyramidInputParams,
        EllipsoidInputParams,
        CylinderInputParams,
        BoxInputParams,
        SphereInputParams,
        ShapePrimitiveInputParams,
    ]


class GeometricSegmentationInputData(BaseModel):
    # provide id here as optional
    segmentation_id: Optional[str]
    # maps timeframe index to list of ShapePrimitiveInputData
    shape_primitives_input: dict[int, list[ShapePrimitiveInputData]]
    time_units: Optional[str]


# END INPUT DATA MODEL


class VolumeMetadata(Protocol):
    def json_metadata(self) -> Metadata: ...

    def db_name(self) -> str: ...

    def entry_id(sefl) -> str: ...

    def segmentation_lattice_ids(self) -> List[str]: ...

    def segmentation_downsamplings(
        self, lattice_id: str
    ) -> List[DownsamplingLevelInfo]: ...

    def volume_downsamplings(self) -> List[DownsamplingLevelInfo]: ...

    def origin(self, downsampling_rate: int) -> List[float]:
        """
        Returns the coordinates of the initial point in Angstroms
        """
        ...

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        """
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        """
        ...

    def grid_dimensions(self, downsampling_rate: int) -> List[int]:
        """
        Returns the number of points along each axis (X, Y, Z)
        """
        ...

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        """
        Returns the number of points along each axis (X, Y, Z) for specific downsampling level
        """
        ...

    def mean(self, level: int, time: int, channel_id: str) -> np.float32:
        """
        Return mean for data at given downsampling level
        """
        ...

    def std(self, level: int, time: int, channel_id: str) -> np.float32:
        """
        Return standard deviation for data at given downsampling level
        """
        ...

    def max(self, level: int, time: int, channel_id: str) -> np.float32:
        """
        Return max for data at given downsampling level
        """
        ...

    def min(self, level: int, time: int, channel_id: str) -> np.float32:
        """
        Return min for data at given downsampling level
        """
        ...

    def mesh_component_numbers(self) -> MeshComponentNumbers:
        """
        Return typed dict with numbers of mesh components (triangles, vertices etc.) for
        each segment, detail level and mesh id
        """
        ...

    def detail_lvl_to_fraction(self) -> dict:
        """
        Returns dict with detail lvls (1,2,3 ...) as keys and corresponding
        mesh simplification ratios (fractions, e.g. 0.8) as values
        """
        ...


class SegmentationPrimaryDescriptor(str, Enum):
    three_d_volume = "three_d_volume"
    mesh_list = "mesh_list"


class InputCase(str, Enum):
    map_only = "map_only"
    map_and_sff = "map_and_sff"
    omezarr = "omezarr"
    ometiff = "ometiff"


class Inputs(BaseModel):
    #    tuple[filename, kind]
    # kinds: 'map', 'sff', 'ome.tiff', 'ome-zarr', 'mask', 'am', 'mod', 'seg', 'custom_annotations' ?
    # depending on files list it runs preprocessing, if application specific - first converts to sff
    files: list[RawInput]


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
