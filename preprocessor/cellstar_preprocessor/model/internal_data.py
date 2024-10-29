import gc
from cellstar_preprocessor.model.map import MapWrapper
from cellstar_preprocessor.model.sff import SFFWrapper
from cellstar_preprocessor.model.tiff_stack import TIFFStackWrapper
from pydantic.dataclasses import dataclass
from pathlib import Path

from cellstar_preprocessor.model.ometiff import OMETIFFWrapper
import zarr
from cellstar_db.models import (
    Annotations,
    DataKind,
    DownsamplingParams,
    EntryData,
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    AssetKind,
    MapParameters,
    Metadata,
    PreparedLatticeSegmentationData,
    PreparedMeshData,
    PreparedMeshSegmentationData,
    PreparedSegmentation,
    PreparedVolume,
    PreparedVolumeData,
    SegmentationExtraData,
    SegmentationKind,
    PrimaryDescriptor,
    StoringParams,
    TimeTransformation,
    VolumeExtraData,
)
from cellstar_preprocessor.flows.constants import (
    ANNOTATIONS_DICT_NAME,
    DEFAULT_ORIGIN,
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    METADATA_DICT_NAME,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.model.omezarr import OMEZarrWrapper
from cellstar_preprocessor.flows.volume.helper_methods import (
    get_origin_from_map_header,
    get_voxel_sizes_from_map_header,
)
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings, open_zarr


@dataclass
class InternalData:
    path: Path
    input_path: Path | list[Path]
    params_for_storing: StoringParams
    downsampling_parameters: DownsamplingParams
    entry_data: EntryData
    input_kind: AssetKind
    data_kind: DataKind
    prepared: PreparedSegmentation | PreparedVolume | None = None
    custom_data: VolumeExtraData | SegmentationExtraData | None = None
    
    def remove_original_resolution(self):
        if self.downsampling_parameters.remove_original_resolution:
            original_res = self.prepared.metadata.original_resolution
            self.prepared.data = [i for i in self.prepared.data if i.resolution != original_res]
        
            self.prepared.metadata.resolutions = [i for i in self.prepared.metadata.resolutions if i != original_res]
        
    def remove_downsamplings(self):
        data_kind = self.data_kind
        match data_kind:
            case DataKind.volume:
                self._remove_downsamplings()
            case DataKind.segmentation:
                self._remove_downsamplings()
            case _:
                raise ValueError(f'Data kind {data_kind} not supported')
    
    
    def _remove_downsamplings(self):
        prepared = self.prepared
        new_prepared_data: list[PreparedVolumeData | PreparedLatticeSegmentationData | PreparedMeshSegmentationData] = []
        original_resolution = prepared.metadata.original_resolution
            
        stored_resolutions: list[int] = []
        for res in prepared.metadata.resolutions:
            size_of_data_for_lvl_mb = self.prepared.compute_size_for_downsampling_level(res)
            print(f"size of data for lvl in mb: {size_of_data_for_lvl_mb}")
            
            if (
                (self.downsampling_parameters.max_size_per_downsampling_lvl_mb
                and size_of_data_for_lvl_mb
                > self.downsampling_parameters.max_size_per_downsampling_lvl_mb)
                or
                (
                    self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                    and size_of_data_for_lvl_mb < self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                )
            ):
                print(f"Data for resolution {res} was removed")
                continue
            
            if self.downsampling_parameters.max_downsampling_level is not None:
                # for downsampling, downsampling_gr in volume_data_gr.groups():
                if res > self.downsampling_parameters.max_downsampling_level:
                    print(f"Data for downsampling {res} was removed")
                    # resolutions_to_be_removed.append(res)
                    continue

            if self.downsampling_parameters.min_downsampling_level is not None:
                # for downsampling, downsampling_gr in volume_data_gr.groups():
                    if (
                        res < self.downsampling_parameters.min_downsampling_level
                        and res != original_resolution
                    ):
                        print(f"Data for downsampling {res} removed for volume")
                        # resolutions_to_be_removed.append(res)
                        continue
            
            stored_resolutions.append(res)
            
        new_prepared_data = [i for i in prepared.data if i.resolution in stored_resolutions]
        
        if len(new_prepared_data) == 0:
            raise Exception(
                f"""No downsamplings will be saved: max_size_per_downsampling_lvl_mb
                {self.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too
                low or other downsampling parameters are too strict"""
            )
        prepared.data = new_prepared_data
        # Fix metadata
        self.prepared.metadata.resolutions = stored_resolutions
    
    def get_first_resolution_group(self, data_group: zarr.Group) -> zarr.Group:
        first_resolution = sorted(data_group.group_keys())[0]
        return data_group[first_resolution]

    def get_first_time_group(self, data_group: zarr.Group) -> zarr.Group:
        first_resolution_gr = self.get_first_resolution_group(data_group)
        first_time: str = sorted(first_resolution_gr.group_keys())[0]
        return first_resolution_gr[first_time]
    
    def get_start_end_time(self, data_group: zarr.Group) -> tuple[int, int]:
        first_resolution_gr = self.get_first_resolution_group(data_group)
        time_intervals = sorted(first_resolution_gr.group_keys())
        time_intervals = sorted(int(x) for x in time_intervals)
        start_time = min(time_intervals)
        end_time = max(time_intervals)
        return (start_time, end_time)

    def get_omezarr_wrapper(self):
        if self.input_kind == AssetKind.omezarr:
            return OMEZarrWrapper(self.input_path)
        else:
            raise ValueError(f"Input kind {self.input_kind} is not {AssetKind.omezarr}")

    def get_tiff_stack_wrapper(self):
        if self.input_kind in {AssetKind.tiff_image_stack_dir, AssetKind.tiff_segmentation_stack_dir}:
            return TIFFStackWrapper(dir_path=self.input_path)
        else:
            raise ValueError(f"Input kind {self.input_kind} is not {AssetKind.tiff_image_stack_dir} or {AssetKind.tiff_segmentation_stack_dir}")
    
    def get_ometiff_wrapper(self):
        if self.input_kind in {AssetKind.ometiff_image, AssetKind.ometiff_segmentation}:
            # exists
            return OMETIFFWrapper(path=self.input_path)
        else:
            raise ValueError(f"Input kind {self.input_kind} is not {AssetKind.ometiff_image} or {AssetKind.ometiff_segmentation}")

    
    def set_time_transformations(self, t: list[TimeTransformation]):
        m = self.get_metadata()
        m.volumes.sampling_info.time_transformations = t
        self.set_metadata(m)

    def get_zarr_root(self):
        return open_zarr(self.path)

    def get_metadata(self):
        d: dict = self.get_zarr_root().attrs[METADATA_DICT_NAME]
        return Metadata.model_validate(d)

    def set_entry_id_in_metadata(self):
        m = self.get_metadata()
        m.entry_id.source_db_name = self.entry_data.source_db_name
        m.entry_id.source_db_id = self.entry_data.source_db_id
        self.set_metadata(m)
        
    def set_entry_id_in_annotations(self):
        a = self.get_annotations()
        a.entry_id.source_db_name = self.entry_data.source_db_name
        a.entry_id.source_db_id = self.entry_data.source_db_id
        self.set_annotations(a)

    def set_metadata(self, m: Metadata):
        self.get_zarr_root().attrs[METADATA_DICT_NAME] = m.model_dump()

    def get_annotations(self):
        d: dict = self.get_zarr_root().attrs[ANNOTATIONS_DICT_NAME]
        return Annotations.model_validate(d)

    def set_annotations(self, a: Annotations):
        self.get_zarr_root().attrs[ANNOTATIONS_DICT_NAME] = a.model_dump()

    def get_volume_data_group(self):
        return self.get_zarr_root()[VOLUME_DATA_GROUPNAME]

    def get_segmentation_data_group(self, kind: SegmentationKind) -> zarr.Group:
        if kind == SegmentationKind.lattice:
            return self.get_zarr_root()[LATTICE_SEGMENTATION_DATA_GROUPNAME]
        elif kind == SegmentationKind.mesh:
            return self.get_zarr_root()[MESH_SEGMENTATION_DATA_GROUPNAME]
        else:
            raise Exception("Segmentation kind is not recognized")

    def get_geometric_segmentation_data(self):
        return [
            GeometricSegmentationData.model_validate(g)
            for g in self.get_geometric_segmentation_data()
        ]

    def get_sff_wrapper(self):
        return SFFWrapper(self.input_path)
    
    
    def get_raw_geometric_segmentation_input_data(self):
        d: dict[str, dict] = self.get_zarr_root().attrs[
            RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS
        ]

        return {
            segmentation_id: GeometricSegmentationInputData.model_validate(gs_input_data)
            for segmentation_id, gs_input_data in d.items()
        }

    def set_geometric_segmentation_data(self, l: list[GeometricSegmentationData]):
        self.get_zarr_root().attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS] = l

    def set_raw_geometric_segmentation_input_data(
        self, models_dict: dict[str, GeometricSegmentationInputData]
    ):
        d = {
            segmentation_id: model.model_dump()
            for segmentation_id, model in models_dict.items()
        }
        self.get_zarr_root().attrs[RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS] = d

    def add_geometric_segmentation_data(self, d: GeometricSegmentationData):
        existing = self.get_geometric_segmentation_data()
        existing.append(d)
        self.set_geometric_segmentation_data(existing)

    def add_raw_geometric_segmentation_input_data(
        self, d: GeometricSegmentationInputData, segmentation_id: str
    ):
        existing = self.get_raw_geometric_segmentation_input_data()
        existing[segmentation_id] = d
        self.set_raw_geometric_segmentation_input_data(existing)

    def get_origin(self):
        kind = self.input_kind
        if kind == AssetKind.map:
            return get_origin_from_map_header(self.map_header)
        elif kind == AssetKind.omezarr:
            w = self.get_omezarr_wrapper()
            m = self.get_metadata()
            boxes = m.volumes.sampling_info.boxes
            multiscale = w.get_image_multiscale()
            datasets_meta = multiscale.datasets
            origin = []
            for idx, level in enumerate(datasets_meta):
                # check index is not in boxes dict for the case of removing original res
                if int(level.path) not in boxes:
                    continue
                if (
                    level.coordinateTransformations[1] is not None
                    and level.coordinateTransformations[1].type == "translation"
                ):
                    normalized_translation_arr = level.coordinateTransformations[
                        1
                    ].get_normalized_space_translation_arr()
                    origin = normalized_translation_arr
                else:
                    origin = DEFAULT_ORIGIN

            # apply global
            if multiscale.coordinateTransformations is not None:
                second_tr = multiscale.coordinateTransformations[1]
                assert second_tr.type == "translation"
                global_tr_arr = second_tr.get_normalized_space_translation_arr()
                assert len(global_tr_arr) == len(normalized_translation_arr)
                # current_voxel_sizes = voxel_sizes[int(level.path)]

                for idx, o in enumerate(origin):
                    origin[idx] = o + global_tr_arr[idx]

            return origin
        elif kind == AssetKind.ometiff_image:
            return DEFAULT_ORIGIN
        else:
            raise NotImplementedError()
        
    def get_voxel_sizes_in_downsamplings(self) -> dict[int, tuple[float, float, float]]:
        voxel_sizes: dict[int, list[float, float, float]] = {}
        kind = self.input_kind
        if kind == AssetKind.map:
            return get_voxel_sizes_from_map_header(
                self.map_header, get_downsamplings(self.get_volume_data_group())
            )
        elif kind == AssetKind.omezarr:
            w = self.get_omezarr_wrapper()
            m = self.get_metadata()
            boxes = m.volumes.sampling_info.boxes
            multiscale = w.get_image_multiscale()
            datasets_meta = multiscale.datasets

            for idx, level in enumerate(datasets_meta):
                # check index is not in boxes dict for the case of removing original res
                if int(level.path) not in boxes:
                    continue
                if level.coordinateTransformations[0].scale is not None:
                    normalized_scale_arr = level.coordinateTransformations[
                        0
                    ].get_normalized_space_scale_arr()

                    voxel_sizes[int(level.path)] = normalized_scale_arr

                    # Then solve multiscale level coord transforms
                if multiscale.coordinateTransformations is not None:
                    first_transform = multiscale.coordinateTransformations[0]
                    assert first_transform.type == "scale"
                    global_scale_arr = first_transform.get_normalized_space_scale_arr()
                    assert len(global_scale_arr) == len(normalized_scale_arr)
                    # current_voxel_sizes = voxel_sizes[int(level.path)]
                    adjusted_voxel_sizes = [
                        global_scale_arr[idx] * value
                        for idx, value in enumerate(voxel_sizes[int(level.path)])
                    ]
                    voxel_sizes[int(level.path)] = adjusted_voxel_sizes
        
        elif kind == AssetKind.ometiff_image:
            w = self.get_ometiff_wrapper()
            # TODO: units
            x = w.reader.ps_x[0]
            y = w.reader.ps_y[0]
            z = w.reader.ps_z[0]
            # for resolution in w.
            # iterate over resolutions in downsampled datada
            for lvl_info in get_downsamplings(self.get_volume_data_group()):
                # an do 
                # TODO: get pixel size somehow from ometiff
                
                if lvl_info.available == True:
                    # x2 = x x2
                    voxel_sizes[lvl_info.level] = [
                        x * lvl_info.level,
                        y * lvl_info.level,
                        z * lvl_info.level            
                    ]
        else: 
            raise NotImplementedError(f"Kind {kind} is not supported yet")
        return voxel_sizes
