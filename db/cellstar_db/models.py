from enum import Enum
from typing import Any, List, Literal, Optional, Protocol, TypedDict, Union

import numpy as np
import zarr
from cellstar_preprocessor.model.input import InputKind, QuantizationDtype
from pydantic import BaseModel


class EntryMetadata(TypedDict):
    description: str | None
    url: str | None


class PreprocessorParameters(TypedDict):
    quantize_dtype_str: QuantizationDtype | None
    quantize_downsampling_levels: list[int] | None
    force_volume_dtype: str | None
    max_size_per_downsampling_lvl_mb: float | None
    min_size_per_downsampling_lvl_mb: float | None
    min_downsampling_level: int | None
    max_downsampling_level: int | None
    remove_original_resolution: bool | None


class RawInputFileResourceInfo(TypedDict):
    kind: Literal["local", "external"]
    uri: str


class RawInputFileInfo(TypedDict):
    kind: InputKind
    resource: RawInputFileResourceInfo
    preprocessor_parameters: PreprocessorParameters | None


class RawInputFilesDownloadParams(TypedDict):
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


class InputForBuildingDatabase(TypedDict):
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
    inputs: list[tuple[str, InputKind]]


class OMETIFFSpecificExtraData(TypedDict):
    # missing_dimension: str
    cell_stage: Optional[str]
    ometiff_source_metadata: Optional[dict]


class VolumeExtraData(TypedDict):
    voxel_size: list[float, float, float] | None
    # map sequential channel ID (e.g. "1" as string)
    # to biologically meaningfull channel id (string)
    channel_ids_mapping: dict[str, str] | None
    dataset_specific_data: object | None


class SegmentationExtraData(TypedDict):
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


class ExtraData(TypedDict):
    entry_metadata: Optional[EntryMetadata]
    volume: Optional[VolumeExtraData]
    segmentation: Optional[SegmentationExtraData]
    # for custom things
    # metadata: Optional[object]
    # dataset_specific_data: Optional[object]


# METADATA DATA MODEL


class SamplingBox(TypedDict):
    origin: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    grid_dimensions: list[int, int, int]


class TimeTransformation(TypedDict):
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, Literal["all"]]
    factor: float


class DownsamplingLevelInfo(TypedDict):
    level: int
    available: bool


class SamplingInfo(TypedDict):
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[DownsamplingLevelInfo]
    # the only thing which changes with SPATIAL downsampling is box!
    boxes: dict[int, SamplingBox]
    time_transformations: Optional[list[TimeTransformation]]
    source_axes_units: dict[str, str]
    # e.g. (0, 1, 2) as standard
    original_axis_order: list[int, int, int]


class TimeInfo(TypedDict):
    kind: str
    start: int
    end: int
    units: str


class SegmentationLatticesMetadata(TypedDict):
    # e.g. label groups (Cell, Chromosomes)
    segmentation_ids: list[str]
    segmentation_sampling_info: dict[str, SamplingInfo]
    time_info: dict[str, TimeInfo]


class GeometricSegmentationSetsMetadata(TypedDict):
    segmentation_ids: list[str]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]


class MeshMetadata(TypedDict):
    num_vertices: int
    num_triangles: int
    num_normals: Optional[int]


class MeshListMetadata(TypedDict):
    mesh_ids: dict[int, MeshMetadata]


class DetailLvlsMetadata(TypedDict):
    detail_lvls: dict[int, MeshListMetadata]


class MeshComponentNumbers(TypedDict):
    segment_ids: dict[int, DetailLvlsMetadata]


class MeshesMetadata(TypedDict):
    # maps timeframe index to MeshComponentNumbers
    mesh_timeframes: dict[int, MeshComponentNumbers]
    detail_lvl_to_fraction: dict


class MeshSegmentationSetsMetadata(TypedDict):
    segmentation_ids: list[str]
    # maps segmentation_id to MeshesMetadata
    segmentation_metadata: dict[str, MeshesMetadata]
    # maps set ids to time info
    time_info: dict[str, TimeInfo]


class VolumeDescriptiveStatistics(TypedDict):
    mean: float
    min: float
    max: float
    std: float


class VolumeSamplingInfo(SamplingInfo):
    # resolution -> time -> channel_id
    descriptive_statistics: dict[int, dict[int, dict[str, VolumeDescriptiveStatistics]]]


class VolumesMetadata(TypedDict):
    channel_ids: list[str]
    # Values of time dimension
    time_info: TimeInfo
    volume_sampling_info: VolumeSamplingInfo


class EntryId(TypedDict):
    source_db_name: str
    source_db_id: str


class ExtraMetadata(TypedDict):
    pre_downsampling_factor: int

class Metadata(TypedDict):
    entry_id: EntryId
    volumes: VolumesMetadata
    extra_metadata: ExtraMetadata | None
    segmentation_lattices: Optional[SegmentationLatticesMetadata]
    segmentation_meshes: Optional[MeshSegmentationSetsMetadata]
    geometric_segmentation: Optional[GeometricSegmentationSetsMetadata]
    entry_metadata: EntryMetadata | None


# END METADATA DATA MODEL

# ANNOTATIONS DATA MODEL


class ChannelAnnotation(TypedDict):
    # uuid
    channel_id: str
    # with transparency
    color: tuple[float, float, float, float]
    label: Optional[str]


class SegmentAnnotationData(TypedDict):
    # label-value in NGFF
    # uuid
    id: Optional[str]

    segment_kind: Literal["lattice", "mesh", "primitive"]
    segment_id: int
    segmentation_id: str
    color: Optional[tuple[float, float, float, float]]
    time: Optional[int | list[int | tuple[int, int]]]
    # other props added later if needed


class ExternalReference(TypedDict):
    # uuid
    id: Optional[str]
    resource: Optional[str]
    accession: Optional[str]
    label: Optional[str]
    description: Optional[str]
    url: Optional[str]


class TargetId(TypedDict):
    segmentation_id: str
    segment_id: int


class DetailsText(TypedDict):
    format: Literal["text", "markdown"]
    text: str


class DescriptionData(TypedDict):
    # uuid
    id: Optional[str]
    target_kind: Literal["lattice", "mesh", "primitive", "entry"]
    target_id: Optional[TargetId]
    name: Optional[str]
    external_references: Optional[list[ExternalReference]]
    is_hidden: Optional[bool]
    time: Optional[int | list[int | tuple[int, int]]]

    details: Optional[DetailsText]
    metadata: Union[dict[str, Any], None]


class AnnotationsMetadata(TypedDict):
    name: Optional[str]
    entry_id: EntryId
    # id => DescriptionData
    descriptions: dict[str, DescriptionData]
    # NOTE: on frontend, segment key = `${kind}:{segmentation_id}:{segment_id}`
    segment_annotations: list[SegmentAnnotationData]
    # Only in SFF
    details: Optional[str]
    volume_channels_annotations: Optional[list[ChannelAnnotation]]


# END ANNOTATIONS DATA MODEL


# "DATA" DATA MODEL


class LatticeSegmentationData(TypedDict):
    grid: zarr.core.Array
    # NOTE: single item in the array which is a Dict
    set_table: zarr.core.Array


class SingleMeshZattrs(TypedDict):
    num_vertices: int
    area: float
    # TODO: add these two
    num_triangles: int
    num_normals: int


class SingleMeshSegmentationData(TypedDict):
    mesh_id: str
    vertices: zarr.core.Array
    triangles: zarr.core.Array
    normals: zarr.core.Array
    attrs: SingleMeshZattrs


class ShapePrimitiveKind(str, Enum):
    sphere = "sphere"
    tube = "tube"
    cylinder = "cylinder"
    box = "box"
    ellipsoid = "ellipsoid"
    pyramid = "pyramid"


class ShapePrimitiveBase(TypedDict):
    # NOTE: to be able to refer to it in annotations
    id: int
    kind: ShapePrimitiveKind
    # NOTE: color in annotations


class RotationParameters(TypedDict):
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


class ShapePrimitiveData(TypedDict):
    shape_primitive_list: list[ShapePrimitiveBase]


class GeometricSegmentationData(TypedDict):
    segmentation_id: str
    # maps timeframe index to ShapePrimitivesData
    primitives: dict[int, ShapePrimitiveData]


class ZarrRoot(TypedDict):
    # resolution => timeframe index => channel
    volume_data: list[dict[int, list[dict[int, list[dict[int, zarr.core.Array]]]]]]
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


class MeshData(TypedDict):
    mesh_id: int
    vertices: np.ndarray  # shape = (n_vertices, 3)
    triangles: np.ndarray  # shape = (n_triangles, 3)
    normals: Optional[np.ndarray]


MeshesData = list[MeshData]


class LatticeSegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: dict
    lattice_id: int


class VolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[LatticeSegmentationSliceData]
    volume_slice: Optional[np.ndarray]
    channel_id: Optional[str]
    time: int


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

    def segmentation_downsamplings(self, lattice_id: str) -> List[DownsamplingLevelInfo]: ...

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
