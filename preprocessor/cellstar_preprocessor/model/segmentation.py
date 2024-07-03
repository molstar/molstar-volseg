from dataclasses import dataclass, field
from typing import Any

from cellstar_db.models import (
    AxisName,
    DetailLvlsMetadata,
    InputKind,
    MeshComponentNumbers,
    MeshesMetadata,
    MeshListMetadata,
    MeshMetadata,
    SamplingInfo,
    SegmentationExtraData,
    SegmentationKind,
    SegmentationPrimaryDescriptor,
)
from cellstar_preprocessor.flows.constants import (
    BLANK_SAMPLING_INFO,
    TIME_INFO_STANDARD,
)
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings
from cellstar_preprocessor.model.internal_data import InternalData


@dataclass
class InternalSegmentation(InternalData):
    custom_data: SegmentationExtraData | None = None
    primary_descriptor: SegmentationPrimaryDescriptor | None = None
    value_to_segment_id_dict: dict = field(default_factory=dict)
    simplification_curve: dict[int, float] = field(default_factory=dict)
    raw_sff_annotations: dict[str, Any] = field(default_factory=object)
    map_headers: dict[str, object] = field(default_factory=dict)

    # def get_voxel_sizes(self):
    #     kind = self.input_kind
    #     if kind == InputKind.sff:
    #         # from metadata
    #         return self.get_metadata().volumes.volume_sampling_info.boxes
    #         # return get_voxel_sizes_from_map_header(self.map_header, get_downsamplings(self.get_volume_data_group()))
    #     # TODO: other

    def set_segmentation_sampling_boxes(self):
        input_kind = self.input_kind
        s = self.get_segmentation_data_group(SegmentationKind.lattice)
        m = self.get_metadata()
        # NOTE: assumes map and sff/mask has same dimension
        # otherwise segmentation does not make sense
        if input_kind in [InputKind.sff, InputKind.mask, InputKind.omezarr]:
            vboxes = m.volumes.sampling_info.boxes
            # should create info gor each lattice and resolution
            for lattice_id, lat_gr in s.groups():
                segm_resoltions = lat_gr.group_keys()
                m.segmentation_lattices.sampling_info[lattice_id] = BLANK_SAMPLING_INFO
                # for res, res_gr in lat_gr.groups():
                sboxes = {k: v for k, v in vboxes.items() if str(k) in segm_resoltions}
                # assert int(res) in vboxes, f'Resolution {res} does not exist in volume data, cannot obtain it'
                m.segmentation_lattices.sampling_info[lattice_id].boxes = sboxes
        # elif input_kind == InputKind.omezarr:
        #     pass
        else:
            raise Exception(f"Input kind {input_kind} is not recognized")
        self.set_metadata(m)

    def set_segmentation_lattices_metadata(self):
        data_gr = self.get_segmentation_data_group(SegmentationKind.lattice)
        m = self.get_metadata()
        if self.input_kind == InputKind.sff:
            original_axis_order = [AxisName.x, AxisName.y, AxisName.z]
        elif self.input_kind in [InputKind.omezarr, InputKind.tiff_segmentation_stack_dir]:
            original_axis_order = m.volumes.sampling_info.original_axis_order
        else:
            raise Exception(f"{self.input_kind} is not supported")

        # m.segmentation_lattices.ids = []
        for lattice_id, lattice_gr in data_gr.groups():
            downsamplings = get_downsamplings(data_group=lattice_gr)
            m.segmentation_lattices.ids.append(lattice_id)

            sampling_info = SamplingInfo(
                spatial_downsampling_levels=downsamplings,
                boxes={},
                time_transformations=[],
                original_axis_order=original_axis_order,
            )
            m.segmentation_lattices.sampling_info[lattice_id] = sampling_info
            m.segmentation_lattices.time_info_mapping[lattice_id] = TIME_INFO_STANDARD

        # till here

        self.set_segmentation_sampling_boxes()
        self.set_metadata(m)

    def set_meshes_metadata(self):
        s = self.get_segmentation_data_group(SegmentationKind.mesh)

        m = self.get_metadata()
        mesh_set_metadata = MeshesMetadata(
            detail_lvl_to_fraction=self.simplification_curve,
            mesh_timeframes={},
        )
        for segmentation_id, segmentation_gr in s.groups():
            for timeframe_index, timeframe_gr in segmentation_gr.groups():
                mesh_comp_num = MeshComponentNumbers(segment_ids={})
                for segment_id, segment in timeframe_gr.groups():
                    detail_lvls_metadata = DetailLvlsMetadata(detail_lvls={})
                    for detail_lvl, detail_lvl_gr in segment.groups():
                        mesh_list_metadata = MeshListMetadata(mesh_ids={})
                        for mesh_id, mesh in detail_lvl_gr.groups():
                            # mesh_metadata: MeshMetadata = {}
                            temp_m = {}
                            for mesh_component_name, mesh_component in mesh.arrays():
                                temp_m[f"num_{mesh_component_name}"] = (
                                    mesh_component.attrs[f"num_{mesh_component_name}"]
                                )
                            mm = MeshMetadata(
                                num_normals=temp_m["num_normals"],
                                num_triangles=temp_m["num_triangles"],
                                num_vertices=temp_m["num_vertices"],
                            )
                            mesh_list_metadata.mesh_ids[int(mesh_id)] = mm
                        detail_lvls_metadata.detail_lvls[int(detail_lvl)] = (
                            mesh_list_metadata
                        )
                    mesh_comp_num.segment_ids[int(segment_id)] = detail_lvls_metadata
                mesh_set_metadata.mesh_timeframes[int(timeframe_index)] = mesh_comp_num

            m.segmentation_meshes.metadata[segmentation_id] = mesh_set_metadata

        self.set_metadata(m)

    def set_segmentation_custom_data(self):
        r = self.get_zarr_root()
        if "extra_data" in r.attrs:
            if "segmentation" in r.attrs["extra_data"]:
                self.custom_data = r.attrs["extra_data"]["segmentation"]
            else:
                self.custom_data = {}
        else:
            self.custom_data = {}
