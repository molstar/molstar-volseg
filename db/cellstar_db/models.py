import copy
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, EnumMeta
from functools import partial, reduce
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Protocol, Set, Tuple, TypedDict, Union
import dask.array as da
from imagecodecs import NoneError
from numpydantic import NDArray, Shape
# from aenum import MultiValueEnum
import mrcfile
# from numpydantic.interface.zarr import ZarrArrayPath

import numpy as np
from pydantic import field_validator
import zarr
from numcodecs import Blosc
from pydantic import BaseModel, ConfigDict, Field, computed_field, conlist



# make to dataclass
@dataclass
class SegmentationSetTable:
    grid: da.Array
    value_to_segment_id_dict: dict[int, int]
    
    def __post_init__(self):
        self.entries: dict = self.__lattice_to_dict_of_sets(self.grid)

    def get_serializable_repr(self) -> Dict:
        """
        Converts sets in self.entries to lists, and returns the whole table as a dict
        """
        d: Dict = copy.deepcopy(self.entries)
        for i in d:
            d[i] = list(d[i])

        return d

    def __lattice_to_dict_of_sets(self, grid: da.Array) -> dict:
        """
        Converts original latice to dict of singletons.
        Each singleton should contain segment ID rather than value
         used to represent that segment in grid
        """
        # can do nonzero instead
        
        
        # d = {}
        # for grid_value_of_segment in unique_values:
        #     if grid_value_of_segment == 0:
        #         d[grid_value_of_segment] = {0}
        #     else:
        #         d[grid_value_of_segment] = {
        #             self.value_to_segment_id_dict[grid_value_of_segment]
        #         }
        
        # TODO: should be dict of sets 
        u: da.Array = da.unique(grid)
        u.compute_chunk_sizes()
        # value 0 is not assigned to any segment, it is just nothing
        # no_zero = u[u != 0]
        # no_zero: da.Array = u[da.nonzero(u)]
        # no_zero.compute_chunk_sizes()
        # TODO: simplify
        # you have unique_values
        # should return dict of them 1: 1, 2: 2 etc.
        # no for loop
        return { i: {i} for i in u.compute().tolist() }

        # d = {}
        # for grid_value_of_segment in unique_values:
        #     if grid_value_of_segment == 0:
        #         d[grid_value_of_segment] = {0}
        #     else:
        #         d[grid_value_of_segment] = {
        #             self.value_to_segment_id_dict[grid_value_of_segment]
        #         }
        #     # here we need a way to access zarr data (segment_list)
        #     # and find segment id for each value (traverse dict backwards)
        #     # and set d[segment_value] = to the found segment id

        # # should return dict without 

        # return d

    def get_categories(self, ids: da.Array) -> Tuple:
        """
        Returns sets from the dict of sets (entries) based on provided IDs
        """
        # gets values of entries
        # need way to get values from dict based on dask array
        # ids = keys
        # values - whatver, can be sets
        # use them to get array of values
        return tuple([self.entries[i] for i in ids.compute()])

    def __find_category(self, target_category: Set) -> Union[int, None]:
        """
        Looks up a category (set) in entries dict, returns its id or None if not found
        """
        for category_id, category in self.entries.items():
            if category == target_category:
                return category_id
        return None

    def __add_category(self, target_category: Set) -> int:
        """
        Adds new category to entries and returns its id
        """
        new_id: int = max(self.entries.keys()) + 1
        self.entries[new_id] = target_category
        return new_id

    def resolve_category(self, target_category: Set):
        """
        Looks up a category (set) in entries dict, returns its id
        If not found, adds new category to entries and returns its id
        """
        category_id = self.__find_category(target_category)
        if category_id is not None:
            return category_id
        else:
            return self.__add_category(target_category)





class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True
    
    @property
    def value(self):
        return self.value


class BaseEnum(Enum, metaclass=MetaEnum):
    pass

class StoreType(str, BaseEnum):
    dir = "dir"
    zip = "zip"

class PrimaryDescriptor(str, BaseEnum):
    three_d_volume = "three_d_volume"
    mesh_list = "mesh_list"
    shape_primitive_list = "shape_primitive_list"

ConlistInt2 = Annotated[list[int], conlist(int, min_length=2, max_length=2)]
ConlistInt3 = Annotated[list[int], conlist(int, min_length=3, max_length=3)]

ConlistFloat3 = Annotated[list[float], conlist(float, min_length=3, max_length=3)]
ConlistFloat4 = Annotated[list[float], conlist(float, min_length=4, max_length=4)]


def hyphenize(field: str):
    return field.replace("_", "-")


# Files:
# NOTE: saved as JSON/Msgpack directly, without temporary storing in .zattrs

# DaskOrNumpyArrayField = partial(Field, default_factory=lambda: np.zeros(10))
# DaskArrayField = partial(Field, default_factory=lambda: da.from_array(np.zeros(10)))

DaskOrNumpyArrayField = NDArray[Shape["* x, * y, * z"], Any]

class DataKind(str, BaseEnum):
    volume = "volume"
    segmentation = "segmentation"

class ModelArbitraryTypes(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class ModelExtra(BaseModel):
    model_config = ConfigDict(extra='allow')

class ModelNoneToDefault(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def not_none(cls, v, val_info):
        """
        Convert None to Default on optional fields.
        Why doesn't Pydantic have this option?
        """
        field = cls.model_fields[val_info.field_name]
        if v is None and (default := field.get_default(call_default_factory=True)) is not None:
            return default
        return v


    



class VolumeChannelAnnotation(BaseModel):
    # uuid
    channel_id: str
    # with transparency
    color: ConlistFloat4 | None = None
    label: Optional[str]

class OMEZarrAxesType(str, BaseEnum):
    space = "space"
    time = "time"
    channel = "channel"


class SpatialAxisUnit(str, BaseEnum):
    micrometer = "micrometer"
    angstrom = "angstrom"
    # TODO: other


class TimeAxisUnit(str, BaseEnum):
    millisecond = "millisecond"


class OMEZarrAxisInfo(ModelExtra):
    name: str
    type: OMEZarrAxesType | None = None
    unit: SpatialAxisUnit | TimeAxisUnit | None = None


def convert_to_angstroms(value: float, input_unit: SpatialAxisUnit):
    # TODO: support other units
    SPACE_UNITS_CONVERSION_DICT = {
        SpatialAxisUnit.micrometer: 10000,
        SpatialAxisUnit.angstrom: 1,
    }

    if input_unit in SPACE_UNITS_CONVERSION_DICT:
        return value * SPACE_UNITS_CONVERSION_DICT[input_unit]
    else:
        raise Exception(f"{input_unit} spatial unit is not supported")

class OMETIFFChannelMetadata(ModelExtra):
    Name : str
    SamplesPerPixel: int
    ExcitationWavelength: float
    ExcitationWavelengthUnit: str

# TODO: develop custom parser instead of pyometiff?
class OMETIFFMetadata(ModelExtra):
    model_config = ConfigDict(populate_by_name=True)
    # TODO: check types
    Directory: str
    Filename: str
    Extension: str
    ImageType: str
    AcqDate: str
    TotalSeries: str
    # TODO: other props
    PhysicalSizeX: str
    PhysicalSizeXUnit: str
    PhysicalSizeY: str
    PhysicalSizeYUnit: str
    PhysicalSizeZ : str
    PhysicalSizeZUnit : str
    SizesBF: str = Field(alias='Sizes BF')
    DimOrderBF: str = Field(alias='DimOrder BF')
    DimOrderBFArray: str = Field(alias='DimOrder BF Array')
    Channels : dict[str, OMETIFFChannelMetadata]


class OMEZarrCoordinateTransformations(ModelExtra):
    type: Literal["scale", "identity", "translation"]
    scale: list[float] | None = None
    translation: list[float] | None = None
    path: str | None = None

    def get_normalized_space_scale_arr(self) -> ConlistFloat3:
        """Normalizes axes order to XYZ and units to Angstroms"""
        # Order
        assert self.type == "scale"
        s = []
        if len(self.scale) == 5:
            s = self.scale[2:]
        elif len(self.scale) == 4:
            s = self.scale[1:]
        else:
            raise Exception("Length of scale arr is not supported")

        normalized_space_scale_arr: ConlistFloat3 = [s[2], s[1], s[0]]
        # to angstroms
        angstroms_scale_arr: ConlistFloat3 = [
            convert_to_angstroms(v) for v in normalized_space_scale_arr
        ]

        return angstroms_scale_arr

    def get_normalized_space_translation_arr(self) -> list[float, float, float]:
        assert self.type == "translation"
        t = []
        if len(self.translation) == 5:
            t = self.translation[2:]
        elif len(self.translation) == 4:
            t = self.translation[1:]
        else:
            raise Exception("Length of translation arr is not supported")

        n: ConlistFloat3 = [t[2], t[1], t[0]]
        # to angstroms
        a: ConlistFloat3 = [convert_to_angstroms(v) for v in n]

        return a


class OMEZarrDatasetsMetadata(ModelExtra):
    coordinateTransformations: list[OMEZarrCoordinateTransformations] 
    path: str


class OmeroChannelMetadata(ModelExtra):
    active: bool
    label: str
    color: str
    # TODO: other fields


class OMEZarrOmeroMetadata(ModelExtra):
    id: int | None  = None
    name: str | None  = None
    version: str | None = None
    channels: list[OmeroChannelMetadata] | None  = None


class OMEZarrMultiscales(ModelExtra):
    axes: list[OMEZarrAxisInfo]
    datasets: list[OMEZarrDatasetsMetadata]
    coordinateTransformations: list[OMEZarrCoordinateTransformations] | None = None
    name: str | None = None
    type: str | None = None


class OMEZarrColorsMetadata(ModelExtra):
    label_value: int
    rgba: ConlistInt3
    
    model_config = ConfigDict(
        alias_generator=hyphenize
    )





class OMEZarrImageLabelMetadata(ModelExtra):
    colors: list[OMEZarrColorsMetadata] | None  = None
    properties: list[object] | None = None
    source: object | None = None
    version: str | None = None


class OMEZarrAttrs(ModelExtra):
    model_config = ConfigDict(
        alias_generator=hyphenize
    )

    # axes: list[OMEZarrAxisInfo] | None  = None
    # datasets: list[OMEZarrDatasetsMetadata] | None  = None
    # coordinateTransformations: list[OMEZarrCoordinateTransformations] | None
    multiscales: list[OMEZarrMultiscales] | None
    omero: OMEZarrOmeroMetadata | None = None
    image_label: OMEZarrImageLabelMetadata | None  = None


class PreprocessorMode(str, BaseEnum):
    add = "add"
    extend = "extend"


class EntryMetadata(BaseModel):
    description: str | None  = None
    url: str | None = None


class QuantizationDtype(str, BaseEnum):
    u1 = "u1"
    u2 = "u2"


class PreprocessorParametersPerEntry(BaseModel):
    """
    Preprocessor parameters for the purpose of
    building database. No working folder, db_path
    """
    quantize_dtype_str: QuantizationDtype | None = None
    quantize_downsampling_levels: list[int] | None = None 
    force_volume_dtype: str | None = None
    max_size_per_downsampling_lvl_mb: float | None = None
    min_size_per_downsampling_lvl_mb: float | None = None
    min_downsampling_level: int | None = None
    max_downsampling_level: int | None = None
    remove_original_resolution: bool | None = None
    pre_downsampling_factor: int | None = None


class SegmentationKind(str, BaseEnum):
    lattice = "lattice"
    mesh = "mesh"
    primitve = "primitive"


# class AssetKind(str, BaseEnum):
#     map = "map"
#     sff = "sff"
#     omezarr = "omezarr"
#     mask = "mask"
#     wrl = "wrl"
#     stl = "stl"
#     seg = "seg"
#     am = "am"
#     custom_annotations = "custom_annotations"
#     nii_volume = "nii_volume"
#     nii_segmentation = "nii_segmentation"
#     geometric_segmentation = "geometric_segmentation"
#     ometiff_image = "ometiff_image"
#     ometiff_segmentation = "ometiff_segmentation"
#     extra_data = "extra_data"
#     tiff_image_stack_dir = "tiff_image_stack_dir"
#     tiff_segmentation_stack_dir = "tiff_segmentation_stack_dir"



TIFF_EXTENSIONS = [".tiff", ".tif"]
MAP_EXTENSIONS = [".map", ".ccp4", ".mrc", ".rec"]
SFF_EXTENSIONS = [".hff"]
OMEZARR_EXTENSIONS = [".zarr"]
NII_EXTENSIONS = [".nii"]
OMETIFF_EXTENSIONS = [".ome.tif", ".ome.tiff"]

# class AssetKind(MultiValueEnum):
#     _init_ = 'value extensions preferred_extension'
#     map = "map", MAP_EXTENSIONS, MAP_EXTENSIONS[0]
#     sff = "sff", SFF_EXTENSIONS, SFF_EXTENSIONS[0]
#     omezarr = "omezarr", OMEZARR_EXTENSIONS, OMEZARR_EXTENSIONS[0] 
#     mask = "mask", MAP_EXTENSIONS, MAP_EXTENSIONS[0]
#     wrl = "wrl", [".wrl"], ".wrl" 
#     stl = "stl", [".stl"], ".stl"
#     seg = "seg", [".seg"], ".seg"
#     am = "am", [".am"], ".am"
#     custom_annotations = "custom_annotations", [".json"], ".json"
#     # TODO: other?
#     nii_volume = "nii_volume", NII_EXTENSIONS, NII_EXTENSIONS[0]
#     nii_segmentation = "nii_segmentation", NII_EXTENSIONS, NII_EXTENSIONS[0]
#     geometric_segmentation = "geometric_segmentation", [".json"], ".json"
#     ometiff_image = "ometiff_image", OMETIFF_EXTENSIONS, OMETIFF_EXTENSIONS[0] 
#     ometiff_segmentation = "ometiff_segmentation", OMETIFF_EXTENSIONS, OMETIFF_EXTENSIONS[0]
#     extra_data = "extra_data", [".json"], ".json"
#     tiff_image_stack_dir = "tiff_image_stack_dir", [], None
#     tiff_segmentation_stack_dir = "tiff_segmentation_stack_dir", [], None


class ParsedMap(ModelArbitraryTypes):
    data: da.Array = DaskOrNumpyArrayField
    header: np.recarray | object

class AssetKind(BaseEnum):
    map = "map", MAP_EXTENSIONS, MAP_EXTENSIONS[0]
    sff = "sff", SFF_EXTENSIONS, SFF_EXTENSIONS[0]
    omezarr = "omezarr", OMEZARR_EXTENSIONS, OMEZARR_EXTENSIONS[0] 
    mask = "mask", MAP_EXTENSIONS, MAP_EXTENSIONS[0]
    wrl = "wrl", [".wrl"], ".wrl" 
    stl = "stl", [".stl"], ".stl"
    seg = "seg", [".seg"], ".seg"
    am = "am", [".am"], ".am"
    custom_annotations = "custom_annotations", [".json"], ".json"
    # TODO: other?
    nii_volume = "nii_volume", NII_EXTENSIONS, NII_EXTENSIONS[0]
    nii_segmentation = "nii_segmentation", NII_EXTENSIONS, NII_EXTENSIONS[0]
    geometric_segmentation = "geometric_segmentation", [".json"], ".json"
    ometiff_image = "ometiff_image", OMETIFF_EXTENSIONS, OMETIFF_EXTENSIONS[0] 
    ometiff_segmentation = "ometiff_segmentation", OMETIFF_EXTENSIONS, OMETIFF_EXTENSIONS[0]
    extra_data = "extra_data", [".json"], ".json"
    tiff_image_stack_dir = "tiff_image_stack_dir", TIFF_EXTENSIONS, TIFF_EXTENSIONS[0]
    tiff_segmentation_stack_dir = "tiff_segmentation_stack_dir", TIFF_EXTENSIONS, TIFF_EXTENSIONS[0]
    
    def __new__(cls, value, extensions, preferred_extension):
        member = object.__new__(cls)
        member._value_ = value
        member.extensions = extensions
        member.preferred_extension = preferred_extension
        return member

class RawInput(BaseModel):
    path: str | Path
    kind: AssetKind
    parameters: PreprocessorParametersPerEntry | None = None


class GeneralPreprocessorParameters(PreprocessorParametersPerEntry):
    """
    Full list of preprocessor arguments
    """

    mode: PreprocessorMode
    entry_id: str
    source_db: str
    source_db_id: str
    source_db_name: str
    working_folder: str
    db_path: str
    inputs: list[RawInput]

class QuantizationInfo(BaseModel):
    min: DaskOrNumpyArrayField
    max: DaskOrNumpyArrayField
    num_steps: int
    src_type: str
    data: DaskOrNumpyArrayField
    to_remove_negatives: DaskOrNumpyArrayField
    
class CompressionFormat(str, BaseEnum):
    zip_dir = "zip"
    # this gonna be a file
    hff_gzipped_file = "hff.gz"
    # this too
    map_gzipped_file = "map.gz"
    # an this
    gzipped_file = "gz"
    # this is folder
    tar_gz_dir = "tar.gz"

class SourceKind(str, BaseEnum):
    local = "local"
    external = "external"

class AssetSourceInfo(BaseModel):
    kind: SourceKind
    uri: str
    compression: CompressionFormat | None = None
    
    @computed_field
    @property
    def name(self) -> str:
        '''Last component after the last slash'''
        return self.uri.split("/")[-1]
    
    
    
    @computed_field
    @property
    def stem(self) -> str:
        '''File name without last suffix'''
        l = self.name.split(".")
        s = ".".join(l[:-1])
        return s
    
    @computed_field
    @property
    def extensions(self) -> str:
        '''All extensions'''
        l = self.name.split(".")
        # s = ".".join(l[1:])
        # return s
        return [f'.{i}' for i in l[1:]]


class AssetInfo(BaseModel):
    kind: AssetKind
    source: AssetSourceInfo
    preprocessor_parameters: PreprocessorParametersPerEntry | None = None
    
    @computed_field
    @property
    def extensions(self) -> list[str]:
        return self.kind.extensions

    @computed_field
    @property
    def preferred_extension(self) -> str:
        return self.kind.preferred_extension

class AssetDownloadParams(BaseModel):
    entry_id: str
    source_db: str
    source_db_id: str
    source_db_name: str
    inputs: list[AssetInfo]


# JSON - list of InputForBuildingDatabase
# TODO: can be a JSON schema instead
# NOTE: Single entry input
# TODO: infer schema from json
# TODO: use this class when parsing
# need to create preprocessor input from


class InputForBuildingDatabase(BaseModel):
    quantize_dtype_str: QuantizationDtype | None = None
    quantize_downsampling_levels: list[int] | None = None
    force_volume_dtype: str | None = None
    max_size_per_downsampling_lvl_mb: float | None = None
    min_size_per_downsampling_lvl_mb: float | None = None
    min_downsampling_level: int | None = None
    max_downsampling_level: int | None = None
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


class DatasetSpecificExtraData(BaseModel):
    ometiff: OMETIFFSpecificExtraData
    
class BaseExtraData(BaseModel):
    dataset_specific_data: DatasetSpecificExtraData | None = None
    voxel_size: ConlistFloat3 | None = None


class PreparedData(ModelArbitraryTypes):
    timeframe_index: int
    resolution: int
    nbytes: float | int | None = None


class PreparedVolumeData(PreparedData):
    channel_num: int
    channel_id: str | None = None
    data: da.Array = DaskOrNumpyArrayField

class PreparedMetadata(BaseModel):
    timeframe_indices: list[int]
    # for meshes gonna be details levels (1, 2, 3, 4 etc.)
    # make sure this is recorded in prepare() method 
    resolutions: list[int]
    
    @computed_field
    @property
    def original_resolution(self) -> int:
        return list(sorted(self.resolutions))[0]
    
class PreparedVolumeMetadata(PreparedMetadata):
    channel_nums: list[int]
    channel_ids: list[str] | None = None

class MeshElementName(str, BaseEnum):
    vertices = "vertices"
    triangles = "triangles"
    normals = "normals"

# TODO: mapping
class PreparedSegmentationMetadata(PreparedMetadata):
    segmentation_ids: list[str] | None = None
    value_to_segment_id_dict: dict[str, dict[int, int]] | None = None

class VedoMeshData(ModelArbitraryTypes):
    vertices: da.Array = DaskOrNumpyArrayField
    triangles: da.Array = DaskOrNumpyArrayField
    normals: da.Array = DaskOrNumpyArrayField
    area: float

class PreparedMeshData(ModelArbitraryTypes):
    vertices: da.Array = DaskOrNumpyArrayField
    triangles: da.Array = DaskOrNumpyArrayField
    normals: da.Array | None = None
    area: float
    segment_id: int
    fraction: int
    mesh_id: int
    # num* will be computed on the fly (vertices.size etc.)

class PreparedMeshSegmentationData(PreparedData):
    segmentation_id: str
    global_mesh_list: list[PreparedMeshData]
    
class PreparedLatticeSegmentationData(PreparedData):
    segmentation_id: str
    data: da.Array = DaskOrNumpyArrayField

class Prepared(BaseModel):
    data: list[PreparedLatticeSegmentationData ] | list[PreparedMeshSegmentationData] | list[PreparedVolumeData]
    
class PreparedVolume(Prepared):
    data: list[PreparedVolumeData]
    metadata: PreparedVolumeMetadata
    
    def compute_size_for_downsampling_level(self, level: int):
        # TODO: meshes
        d = list(filter(lambda i: i.resolution == level, self.data))
        sizes = [i.data.nbytes for i in d]
        r = sum(sizes)
        # r is 0
        r_in_mb = r / 1024**2
        # print(f"Size of data for resolution {level} in mb: {r_in_mb}")
        return r_in_mb
        # r = reduce(lambda idx, item: item.data.size, d, 0) 
    
class DownsamplingLevelDict(ModelArbitraryTypes):
    ratio: int
    grid: da.Array = DaskOrNumpyArrayField
    set_table: SegmentationSetTable

class PreparedLatticeSegmentationData(PreparedData):
    segmentation_id: str
    data: da.Array = DaskOrNumpyArrayField

class PreparedSegmentation(Prepared):
    data: list[PreparedLatticeSegmentationData ] | list[PreparedMeshSegmentationData]
    metadata: PreparedSegmentationMetadata
    
    kind: SegmentationKind
    
    def compute_size_for_downsampling_level(self, level: int):
        match self.kind:
            case SegmentationKind.lattice:
                # TODO: meshes
                data: list[PreparedLatticeSegmentationData] = self.data
                d: list[PreparedLatticeSegmentationData] = list(filter(lambda i: i.resolution == level, data))
                sizes = [i.data.nbytes for i in d]
                r = sum(sizes)
                # r is 0
                r_in_mb = r / 1024**2
                # print(f"Size of data for resolution {level} in mb: {r_in_mb}")
                return r_in_mb
                # r = reduce(lambda idx, item: item.data.size, d, 0)
            case SegmentationKind.mesh:
                data: list[PreparedMeshSegmentationData] = self.data
                d: list[PreparedMeshSegmentationData] = list(filter(lambda i: i.resolution == level, data))
                mesh_list: list[PreparedMeshData] = []
                for item in d:
                    mesh_list = mesh_list + item.global_mesh_list
                
                sum_size = int(0)
                for i in mesh_list:
                    sum_size = sum_size + i.vertices.nbytes + i.triangles.nbytes
                    if i.normals is not None:
                        sum_size = sum_size + i.normals.nbytes
                
                r_in_mb = sum_size / 1024**2
                return r_in_mb
    
class VolumeExtraData(BaseExtraData):
    # map sequential channel ID (e.g. "1" as string)
    # to biologically meaningfull channel id (string)
    channel_ids_mapping: dict[str, str] | None = None
    custom_volume_channel_annotations: list[VolumeChannelAnnotation] | None = None 

class MapParameters(ModelArbitraryTypes):
    voxel_size: ConlistFloat3 | None = None
    dtype: str | np.dtype | None = None


class MapHeader(ModelArbitraryTypes):
    mrcfile_header: np.recarray
    # NC: int | None = None
    # NR: int | None
    # NS: int
    # NCSTART: int
    # NRSTART: int
    # NSSTART: int
    # xLength: float
    # yLength: float
    # zLength: float
    # MAPC: int
    # MAPR: int
    # MAPS: int
    
    # @classmethod
    def __init__(self, mrcfile_header: np.recarray):    
        self.NC, self.NR, self.NS = int(mrcfile_header.nx), int(mrcfile_header.ny), int(mrcfile_header.nz)
        self.NCSTART, self.NRSTART, self.NSSTART = (
            int(mrcfile_header.nxstart),
            int(mrcfile_header.nystart),
            int(mrcfile_header.nzstart),
        )
        self.xLength = round(Decimal(float(mrcfile_header.cella.x)), 5)
        self.yLength = round(Decimal(float(mrcfile_header.cella.y)), 5)
        self.zLength = round(Decimal(float(mrcfile_header.cella.z)), 5)
        self.MAPC, self.MAPR, self.MAPS = int(mrcfile_header.mapc), int(mrcfile_header.mapr), int(mrcfile_header.maps)

    @computed_field
    @property
    def voxel_size(self) -> ConlistFloat3:
        ao = {self.MAPC - 1: 0, self.MAPR - 1: 1, self.MAPS - 1: 2}

        N = self.NC, self.NR, self.NS
        N = N[ao[0]], N[ao[1]], N[ao[2]]

        START = self.NCSTART, self.NRSTART, self.NSSTART
        START = START[ao[0]], START[ao[1]], START[ao[2]]

        original_voxel_size: tuple[float, float, float] = (
            self.xLength / N[0],
            self.yLength / N[1],
            self.zLength / N[2],
        )
        return original_voxel_size

    
class SegmentationExtraData(BaseExtraData):
    # map segmentation number (dimension) in case of >3D array (e.g. OMETIFF)
    # or in case segmentation ids are given as numbers by default
    # to segmentation id (string)
    segmentation_ids_mapping: dict[str, str] | None = None
    # CURRENTLY IS A KEY THAT IS PROVIDED IN SEGMENTATION_IDS_MAPPING
    segment_ids_to_segment_names_mapping: dict[str, dict[str, str]] | None = None


class ExtraData(BaseModel):
    entry_metadata: Optional[EntryMetadata]
    volume: Optional[VolumeExtraData]
    segmentation: Optional[SegmentationExtraData]
    # for custom things
    # metadata: Optional[object]
    # dataset_specific_data: Optional[object]


# METADATA DATA MODEL


class SamplingBox(BaseModel):
    origin: ConlistFloat3
    voxel_size: ConlistFloat3
    grid_dimensions: ConlistInt3


class TimeTransformation(BaseModel):
    # to which downsampling level it is applied: can be to specific level, can be to all lvls
    downsampling_level: Union[int, Literal["all"]]
    factor: float

class DimensionSizes(BaseModel):
    X: int
    Y: int
    Z: int
    T: int
    C: int
    

class AxisName(str, BaseEnum):
    x = "x"
    y = "y"
    z = "z"
    t = "t"
    c = "c"
    
class DownsamplingLevelInfo(BaseModel):
    level: int
    available: bool
    ratio_per_dimension: dict[AxisName, float] | None = None


class MeshZattrs(ModelNoneToDefault):
    num_vertices: int | None = None
    num_triangles: int | None = None
    num_normals: int | None = None
    area: float | None = None

class SamplingInfo(BaseModel):
    # Info about "downsampling dimension"
    spatial_downsampling_levels: list[DownsamplingLevelInfo]
    # the only thing which changes with SPATIAL downsampling is box!
    boxes: dict[int, SamplingBox]
    time_transformations: Optional[list[TimeTransformation]]
    original_axis_order: list[AxisName]
    source_axes_units: dict[AxisName, SpatialAxisUnit | TimeAxisUnit] = Field(default_factory=dict)
    

# TODO:
class TimeInfo(BaseModel):
    kind: Literal["range"]
    start: int
    end: int
    units: Literal["millisecond"]


class SegmentationLatticesMetadata(BaseModel):
    # e.g. label groups (Cell, Chromosomes)
    ids: list[str]
    sampling_info: dict[str, SamplingInfo]
    time_info_mapping: dict[str, TimeInfo]


class GeometricSegmentationsMetadata(BaseModel):
    ids: list[str]
    # maps set ids to time info
    time_info_mapping: dict[str, TimeInfo]


class MeshMetadata(BaseModel):
    num_vertices: int
    num_triangles: int
    num_normals: int | None = None


class MeshListMetadata(BaseModel):
    mesh_ids: dict[int, MeshMetadata]


class DetailLvlsMetadata(BaseModel):
    detail_lvls: dict[int, MeshListMetadata]


class MeshComponentNumbers(BaseModel):
    segment_ids: dict[int, DetailLvlsMetadata]


class MeshesMetadata(BaseModel):
    # maps timeframe index to MeshComponentNumbers
    mesh_timeframes: dict[int, MeshComponentNumbers]
    detail_lvl_to_fraction: dict[int, float]


class MeshSegmentationsMetadata(BaseModel):
    ids: list[str]
    # maps segmentation_id to MeshesMetadata
    # no meshes metadata in actin
    metadata: dict[str, MeshesMetadata]
    # maps set ids to time info
    time_info_mapping: dict[str, TimeInfo]


class VolumeDescriptiveStatistics(BaseModel):
    mean: float
    min: float
    max: float
    std: float


class VolumeSamplingInfo(SamplingInfo):
    # resolution -> time -> channel_id
    descriptive_statistics: dict[int, dict[int, dict[str, VolumeDescriptiveStatistics]]] = Field(default_factory=dict)


class VolumesMetadata(BaseModel):
    channel_ids: list[str]
    # Values of time dimension
    time_info: TimeInfo
    sampling_info: VolumeSamplingInfo


class ExtraMetadata(BaseModel):
    pass
    # pre_downsampling_factor: int | None = None


class EntryId(BaseModel):
    source_db_name: str
    source_db_id: str



class Metadata(BaseModel):
    entry_id: EntryId
    volumes: VolumesMetadata | None = None
    segmentation_lattices: Optional[SegmentationLatticesMetadata]
    segmentation_meshes: Optional[MeshSegmentationsMetadata]
    geometric_segmentation: Optional[GeometricSegmentationsMetadata]
    extra_metadata: ExtraMetadata | None = None


class SegmentAnnotationData(BaseModel):
    # label-value in NGFF
    # uuid
    id: Optional[str]
    segment_kind: SegmentationKind
    segment_id: int
    segmentation_id: str
    color: ConlistFloat4 | None = None
    time: Optional[int | list[int | ConlistInt2]]
    # other props added later if needed


class ExternalReference(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    
    id: Optional[str] = None
    resource: Optional[str] = None
    accession: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None


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
    time: Optional[int | list[int | ConlistInt2]]

    details: Optional[DetailsText]
    metadata: Union[dict[str, Any], None]


class Annotations(BaseModel):
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


class LatticeSegmentationData(ModelArbitraryTypes):
    grid: zarr.Array = DaskOrNumpyArrayField
    # NOTE: single item in the array which is a Dict
    # TODO: should be dask zatts or whatever
    set_table: zarr.Array = DaskOrNumpyArrayField

class SingleMeshZattrs(BaseModel):
    num_vertices: int
    area: float
    num_triangles: int
    num_normals: int


class SingleMeshSegmentationData(ModelArbitraryTypes):
    mesh_id: str
    vertices: zarr.Array = DaskOrNumpyArrayField
    triangles: zarr.Array = DaskOrNumpyArrayField
    normals: zarr.Array | None = None
    attrs: SingleMeshZattrs


class ShapePrimitiveKind(str, BaseEnum):
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
    axis: ConlistFloat3
    radians: float


class Sphere(ShapePrimitiveBase):
    # in angstroms
    center: ConlistFloat3
    radius: float


class Box(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: ConlistFloat3
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: ConlistFloat3
    rotation: RotationParameters


class Cylinder(ShapePrimitiveBase):
    start: ConlistFloat3
    end: ConlistFloat3
    radius_bottom: float
    radius_top: float  # =0 <=> cone


class Ellipsoid(ShapePrimitiveBase):
    dir_major: ConlistFloat3
    dir_minor: ConlistFloat3
    center: ConlistFloat3
    radius_scale: ConlistFloat3


class Pyramid(ShapePrimitiveBase):
    # with respect to origin 0, 0, 0
    translation: ConlistFloat3
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: ConlistFloat3
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




class MeshData(ModelArbitraryTypes):
    mesh_id: int
    vertices: DaskOrNumpyArrayField  # shape = (n_vertices, 3)
    triangles: DaskOrNumpyArrayField  # shape = (n_triangles, 3)
    normals: DaskOrNumpyArrayField | None  = None

MeshesData = list[MeshData]


class LatticeSegmentationSliceData(ModelArbitraryTypes):
    # array with set ids
    category_set_ids: np.ndarray = Field(default_factory=lambda: np.zeros(10))
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: dict
    lattice_id: int

class SliceData(ModelArbitraryTypes):
    segmentation_slice: LatticeSegmentationSliceData | None = None
    volume_slice: Optional[np.ndarray] = Field(default_factory=lambda: np.zeros(10))
    channel_id: Optional[str]
    time: int


# END SERVER OUTPUT DATA MODEL

# INPUT DATA MODEL


class ShapePrimitiveInputParams(BaseModel):
    id: int
    color: ConlistFloat4


class RotationInputParameters(BaseModel):
    axis: ConlistFloat3
    radians: float


class SphereInputParams(ShapePrimitiveInputParams):
    center: ConlistFloat3
    radius: float


class BoxInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: ConlistFloat3
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: ConlistFloat3
    rotation: RotationInputParameters


class CylinderInputParams(ShapePrimitiveInputParams):
    start: ConlistFloat3
    end: ConlistFloat3
    radius_bottom: float
    radius_top: float  # =0 <=> cone


class EllipsoidInputParams(ShapePrimitiveInputParams):
    dir_major: ConlistFloat3
    dir_minor: ConlistFloat3
    center: ConlistFloat3
    radius_scale: ConlistFloat3


class PyramidInputParams(ShapePrimitiveInputParams):
    # with respect to origin 0, 0, 0
    translation: ConlistFloat3
    # default size 2, 2, 2 in angstroms for pdbe-1.rec
    scaling: ConlistFloat3
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
    
    
GeometricSegmentationJson = list[GeometricSegmentationData]


# END INPUT DATA MODEL


class VolumeMetadata(Protocol):
    def model(self) -> Metadata: ...
    def dict(self) -> dict: ...

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



class InputCase(str, BaseEnum):
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


class DownsamplingParams(ModelNoneToDefault):
    max_size_per_downsampling_lvl_mb: Optional[float] = None
    min_size_per_downsampling_lvl_mb: Optional[float] = None
    min_downsampling_level: Optional[int] = None
    max_downsampling_level: Optional[int] = None
    remove_original_resolution: Optional[bool] = False
    
    # class Config:
    #     validate_assignment = True

    # @validator('min_size_per_downsampling_lvl_mb')
    # def set_min_size_per_downsampling_lvl_mb(cls, min_size_per_downsampling_lvl_mb):
    #     return min_size_per_downsampling_lvl_mb or 5.0
    
    # @validator('remove_original_resolution')
    # def set_remove_original_resolution(cls, remove_original_resolution):
    #     return remove_original_resolution or False



class ChunkingMode(MetaEnum):
    auto = "auto"
    custom_function = "custom_function"
    false = "false"

class StoringParams(ModelArbitraryTypes):
    #  params_for_storing
    # 'auto'
    chunking_mode: ChunkingMode = ChunkingMode.auto
    # Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0)
    # TODO: figure out how to pass it
    compressor: object = Blosc(
        cname="lz4", clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0
    )
    # we use only 'zip'
    store_type: StoreType = StoreType.zip


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
    downsampling: DownsamplingParams
    entry_data: EntryData
    # for intermediate data
    working_folder: Path

    # do we need these two here?
    # storing params perhaps should be here as temporary internal format (zarr) also uses them
    db_path: Path
    storing_params: StoringParams
    # add_segmentation_to_entry: bool = False
    # add_custom_annotations: bool = False
    custom_data: dict[str, Any] | None = None



class Software(BaseModel):
    name: str | None = None
    version: str | None = None
    processing_details: str | None = None

class TransformationMatrix(BaseModel):
    id: int
    rows: int
    cols: int
    data: str

class BoundingBox(BaseModel):
    xmin: object
    xmax: object
    ymin: object
    ymax: object
    zmin: object
    zmax: object

class BiologicalAnnotation(BaseModel):
    name: str | None = None
    description: str | None = None
    number_of_instances: int | None = None
    external_references: list[ExternalReference] = []

class ShapePrimitiveBaseSFF(BaseModel):
    pass

class ConeSFF(ShapePrimitiveBaseSFF):
    height: object
    bottom_radius: object
    transform_id: int
    attribute: float
    
class CuboidSFF(ShapePrimitiveBaseSFF):
    x: object
    y: object
    z: object
    transform_id: object
    attribute: float

class CylinderSFF(ShapePrimitiveBaseSFF):
    height: object
    diameter: object
    transform_id: int
    attribute: float

class EllipsoidSFF(ShapePrimitiveBaseSFF):
    x: object
    y: object
    z: object
    transform_id: object
    attribute: float


    


class ThreeDVolume(BaseModel):
    lattice_id: int
    value: float
    transform_id: int | None = None
    # TODO: typecast "value" to int in separate function



class VolumeIndexType(BaseModel):
    rows: int
    cols: int
    sections: int

class VolumeStructureType(BaseModel):
    rows: int
    cols: int
    sections: int

    def to_tuple(self):
        return (self.cols, self.rows, self.sections)

class Endianness(str, BaseEnum):
    little = "little"
    big = "big"

class ModeSFFDataType(str, BaseEnum):
    int8 = "int8"
    uint8 = "uint8"
    int16 = "int16"
    uint16 = "uint16"
    int32 = "int32"
    uint32 = "uint32"
    int64 = "uint64"
    uint64 = "uint64"
    float32 = "float32"
    float64 = "float64"
    
class LatticeSFF(BaseModel):
    id: int
    mode: ModeSFFDataType
    endianness: Endianness
    size: VolumeStructureType
    start: VolumeIndexType
    data: str

class MeshElementBaseSFF(BaseModel):
    mode: ModeSFFDataType
    endianness: Endianness
    data: str

class VertexSFF(MeshElementBaseSFF):
    num_vertices: int

class NormalSFF(MeshElementBaseSFF):
    num_normals: int
    
class TrianglesSFF(MeshElementBaseSFF):
    num_triangles: int

class MeshSFF(BaseModel):
    # in mesh list, usually a single one in mesh list
    id: int
    vertices: VertexSFF
    normals: NormalSFF | None = None
    triangles: TrianglesSFF
    transform_id: int | None = None



class Segment(BaseModel):
    id: int
    parent_id: int
    biological_annotation: BiologicalAnnotation | None
    colour: ConlistFloat4
    mesh_list: list[MeshSFF] | None  = []
    three_d_volume: ThreeDVolume | None = None
    shape_primitive_list: list[ShapePrimitiveBaseSFF] = []
    
class SFFSegmentationModel(BaseModel):
    version: str | None = None
    name: str | None = None
    software_list: list[Software] = []
    transfrom_list: list[TransformationMatrix] = []
    primary_descriptor: PrimaryDescriptor
    bounding_box: BoundingBox | None = None
    global_external_references: list[ExternalReference] = []
    segment_list: list[Segment] = []
    lattice_list: list[LatticeSFF] = [] 
    details: str | None = None
    
    

class Info(BaseModel):
    metadata: Metadata
    annotations: Annotations