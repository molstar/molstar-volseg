from dataclasses import dataclass
from pathlib import Path

from cellstar_preprocessor.flows.volume.helper_methods import get_origin_from_map_header, get_voxel_sizes_from_map_header
import zarr
from cellstar_db.models import (
    AnnotationsMetadata,
    DownsamplingParams,
    EntryData,
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    InputKind,
    Metadata,
    SegmentationKind,
    TimeTransformation,
)
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.omezarr import OMEZarrWrapper
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings, open_zarr


@dataclass
class InternalData:
    path: Path
    input_path: Path | list[Path]
    params_for_storing: dict
    downsampling_parameters: DownsamplingParams
    entry_data: EntryData
    input_kind: InputKind

    def get_first_resolution_group(self, data_group: zarr.Group) -> zarr.Group:
        first_resolution = sorted(data_group.group_keys())[0]
        return data_group[first_resolution]

    def get_first_time_group(self, data_group: zarr.Group) -> zarr.Group:
        first_resolution_gr = self.get_first_resolution_group(data_group)
        first_time: str = sorted(first_resolution_gr.group_keys())[0]
        return first_resolution_gr[first_time]

    def get_first_channel_array(self, data_group: zarr.Group) -> zarr.Array:
        first_time_gr = self.get_first_time_group(data_group)
        first_channel: str = sorted(first_time_gr.array_keys())[0]
        return first_time_gr[first_channel]

    def get_start_end_time(self, data_group: zarr.Group) -> tuple[int, int]:
        first_resolution_gr = self.get_first_resolution_group(data_group)
        time_intervals = sorted(first_resolution_gr.group_keys())
        time_intervals = sorted(int(x) for x in time_intervals)
        start_time = min(time_intervals)
        end_time = max(time_intervals)
        return (start_time, end_time)

    def get_label_resolutions(self):
        return list(self.get_zarr_root().group_keys())
    
    def get_label_group(self):
        return self.get_zarr_root().labels
    
    def get_label_resolutions(self, label_gr_name: str):
        return list(self.get_label_group()[label_gr_name].group_keys())
    
    def get_omezarr_wrapper(self):
        return OMEZarrWrapper(self.input_path)

    def set_time_transformations(self, t: list[TimeTransformation]):
        m = self.get_metadata()
        m.volumes.sampling_info.time_transformations = t
        self.set_metadata(m)

    def get_zarr_root(self):
        return open_zarr(self.path)

    def get_metadata(self):
        d: dict = self.get_zarr_root().attrs["metadata_dict"]
        return Metadata.parse_obj(d)

    def set_entry_id_in_metadata(self):
        m = self.get_metadata()
        m.entry_id.source_db_name = self.entry_data.source_db_name
        m.entry_id.source_db_id = self.entry_data.source_db_id
        self.set_metadata(m)

    def set_metadata(self, m: Metadata):
        self.get_zarr_root().attrs["metadata_dict"] = m.dict()

    def get_annotations(self):
        d: dict = self.get_zarr_root().attrs["annotations_dict"]
        return AnnotationsMetadata.parse_obj(d)

    def set_annotations(self, a: AnnotationsMetadata):
        self.get_zarr_root().attrs["annotations_dict"] = a.dict()

    def get_volume_data_group(self):
        return self.get_zarr_root()[VOLUME_DATA_GROUPNAME]

    def get_segmentation_data_group(self, kind: SegmentationKind):
        if kind == SegmentationKind.lattice:
            return self.get_zarr_root()[LATTICE_SEGMENTATION_DATA_GROUPNAME]
        elif kind == SegmentationKind.mesh:
            return self.get_zarr_root()[MESH_SEGMENTATION_DATA_GROUPNAME]
        else:
            raise Exception("Segmentation kind is not recognized")

    def get_geometric_segmentation_data(self):
        return [
            GeometricSegmentationData.parse_obj(g)
            for g in self.get_geometric_segmentation_data()
        ]

    def get_raw_geometric_segmentation_input_data(self):
        d: dict[str, dict] = self.get_zarr_root().attrs[
            RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS
        ]

        return {
            segmentation_id: GeometricSegmentationInputData.parse_obj(gs_input_data)
            for segmentation_id, gs_input_data in d.items()
        }

    def set_geometric_segmentation_data(self, l: list[GeometricSegmentationData]):
        self.get_zarr_root().attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS] = l

    def set_raw_geometric_segmentation_input_data(
        self, models_dict: dict[str, GeometricSegmentationInputData]
    ):
        d = {
            segmentation_id: model.dict()
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
        if kind == InputKind.map:
            return get_origin_from_map_header(self.map_header)
        elif kind == InputKind.omezarr:
            w = self.get_omezarr_wrapper()
            m = self.get_metadata()
            boxes = m.volumes.sampling_info.boxes
            multiscale = w.get_multiscale()
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
                    origin = [0.0, 0.0, 0.0]

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

    def get_voxel_sizes_in_downsamplings(self) -> dict[int, tuple[float, float, float]]:
        voxel_sizes: dict[int, tuple[float, float, float]] = {}
        kind = self.input_kind
        if kind == InputKind.map:
            return get_voxel_sizes_from_map_header(
                self.map_header, get_downsamplings(self.get_volume_data_group())
            )
        elif kind == InputKind.omezarr:
            w = self.get_omezarr_wrapper()
            m = self.get_metadata()
            boxes = m.volumes.sampling_info.boxes
            multiscale = w.get_multiscale()
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

        return voxel_sizes
